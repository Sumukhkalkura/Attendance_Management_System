/* Administrator dashboard: overview, users (FR-07), classes and subjects
   (FR-08), enrollments (FR-09) and attendance reports (FR-04/FR-05). */

"use strict";

const { api, el, $, iconButton, avatarCell, badge, roleBadge, progress, formatDate,
    stateRow, fillRows, fillSelect, toast, withLoading, confirmAction, formDialog } = App;

const state = {
    me: null,
    users: [],
    classes: [],
    subjects: [],
    enrollments: []
};

const byName = (a, b) => a.name.localeCompare(b.name);
const activeTeachers = () => state.users.filter((u) => u.role === "teacher" && u.active);
const teacherOptions = () => activeTeachers().map((t) => ({ id: t.id, name: t.username }));

async function loadUsers() {
    state.users = (await api("/api/users")).users;
}

async function loadClasses() {
    const classes = (await api("/api/classes")).classes;

    // Each class's subjects come from the class-subject association endpoint.
    const subjectLists = await Promise.all(
        classes.map((c) => api(`/api/classes/${c.id}/subjects`).then((r) => r.subjects))
    );
    classes.forEach((c, i) => { c.subjects = subjectLists[i]; });

    state.classes = classes;
}

async function loadSubjects() {
    state.subjects = (await api("/api/subjects")).subjects.sort(byName);
}

async function loadEnrollments() {
    state.enrollments = (await api("/api/enrollments")).enrollments;
}

function matches(text, query) {
    return text.toLowerCase().includes(query.trim().toLowerCase());
}

// =====================================================================
// Overview
// =====================================================================

async function showOverview() {
    const lowTable = $("#lowAttendanceTable");
    stateRow(lowTable, 3, "loading");

    try {
        const [, , , percentages] = await Promise.all([
            loadUsers(), loadClasses(), loadSubjects(), api("/api/attendance/percentages")
        ]);

        const countRole = (role) => state.users.filter((u) => u.role === role).length;
        $("#statStudents").textContent = countRole("student");
        $("#statTeachers").textContent = countRole("teacher");
        $("#statClasses").textContent = state.classes.length;
        $("#statSubjects").textContent = state.subjects.length;

        const students = percentages.students;
        const attended = students.reduce((sum, s) => sum + s.classes_attended, 0);
        const total = students.reduce((sum, s) => sum + s.total_classes, 0);

        $("#statOverall").textContent = total ? App.formatPercent(Math.round(attended / total * 1000) / 10) : "–";
        $("#statOverallSub").textContent = total ? `${attended} of ${total} marked classes` : "No attendance marked yet";

        const low = students
            .filter((s) => s.total_classes > 0 && s.attendance_percentage < 75)
            .sort((a, b) => a.attendance_percentage - b.attendance_percentage)
            .slice(0, 8);

        fillRows(lowTable, 3, low.map((s) => [
            avatarCell(s.student_name),
            el("td", { className: "num", text: `${s.classes_attended} / ${s.total_classes}` }),
            progress(s.attendance_percentage)
        ]), "Everyone is on track", "No student with attendance records is below 75%.");

    } catch (error) {
        stateRow(lowTable, 3, "error", "Could not load overview", error.message);
    }
}

// =====================================================================
// Users (FR-07)
// =====================================================================

const userDialog = formDialog($("#userDialog"), async (form) => {
    const userId = form.dataset.userId;
    const username = form.username.value.trim();
    const password = form.password.value;
    const body = { username, role: form.role.value };

    if (password) body.password = password;

    if (userId) {
        const editingSelf = Number(userId) === state.me.id;
        if (editingSelf && body.role !== "admin") {
            throw new Error("You cannot remove your own administrator role.");
        }
        await api(`/api/users/${userId}`, { method: "PATCH", body });
        toast(`Updated ${username}.`);
    } else {
        await api("/api/users", { method: "POST", body });
        toast(`Created ${body.role} account "${username}".`);
    }

    await loadUsers();
    renderUsers();
});

function openUserDialog(user) {
    userDialog.open((form) => {
        form.dataset.userId = user ? user.id : "";
        $("#userDialogTitle").textContent = user ? `Edit ${user.username}` : "New user";
        $("#userPasswordLabel").textContent = user ? "New password (optional)" : "Password";
        $("#userPasswordHint").textContent = user
            ? "Leave blank to keep the current password."
            : "At least 8 characters.";
        form.password.required = !user;
        form.username.value = user ? user.username : "";
        form.role.value = user ? user.role : "student";
    });
}

async function toggleUserActive(user) {
    const deactivating = Boolean(user.active);

    const ok = await confirmAction({
        title: deactivating ? `Deactivate ${user.username}?` : `Activate ${user.username}?`,
        message: deactivating
            ? "They will no longer be able to sign in. Their attendance records are kept."
            : "They will be able to sign in again.",
        confirmLabel: deactivating ? "Deactivate" : "Activate",
        danger: deactivating
    });

    if (!ok) return;

    try {
        await api(`/api/users/${user.id}/${deactivating ? "deactivate" : "activate"}`, { method: "POST" });
        toast(`${user.username} ${deactivating ? "deactivated" : "activated"}.`);
        await loadUsers();
        renderUsers();
    } catch (error) {
        toast(error.message, "error");
    }
}

function renderUsers() {
    const query = $("#userSearch").value;
    const role = $("#userRoleFilter").value;
    const status = $("#userStatusFilter").value;

    const users = state.users.filter((u) =>
        matches(u.username, query)
        && (!role || u.role === role)
        && (!status || String(u.active) === status)
    );

    fillRows($("#usersTable"), 4, users.map((user) => {
        const isSelf = user.id === state.me.id;

        const toggle = iconButton("power", user.active ? "Deactivate" : "Activate", () => toggleUserActive(user));
        if (isSelf) {
            toggle.disabled = true;
            toggle.title = "You cannot deactivate your own account";
        }

        return [
            avatarCell(user.username, isSelf ? "You" : `ID ${user.id}`),
            roleBadge(user.role),
            user.active ? badge("Active", "green") : badge("Inactive", "gray"),
            el("td", {}, el("div", { className: "actions" },
                iconButton("edit", "Edit", () => openUserDialog(user)),
                toggle
            ))
        ];
    }), "No users found", "Try a different search or filter.");
}

async function showUsers(firstVisit) {
    if (firstVisit) {
        ["#userSearch", "#userRoleFilter", "#userStatusFilter"].forEach((id) =>
            $(id).addEventListener("input", renderUsers)
        );
        $("#newUserButton").addEventListener("click", () => openUserDialog(null));
    }

    stateRow($("#usersTable"), 4, "loading");

    try {
        await loadUsers();
        renderUsers();
    } catch (error) {
        stateRow($("#usersTable"), 4, "error", "Could not load users", error.message);
    }
}

// =====================================================================
// Classes (FR-08)
// =====================================================================

const classDialog = formDialog($("#classDialog"), async (form) => {
    const classId = form.dataset.classId;
    const teacherId = form.teacher_id.value ? Number(form.teacher_id.value) : null;
    const body = { name: form.name.value.trim(), teacher_id: teacherId };

    if (classId) {
        await api(`/api/classes/${classId}`, { method: "PATCH", body });
        toast(`Updated class "${body.name}".`);
    } else {
        await api("/api/classes", { method: "POST", body });
        toast(`Created class "${body.name}".`);
    }

    await loadClasses();
    renderClasses();
});

function openClassDialog(cls) {
    classDialog.open((form) => {
        form.dataset.classId = cls ? cls.id : "";
        $("#classDialogTitle").textContent = cls ? `Edit ${cls.name}` : "New class";
        fillSelect(form.teacher_id, teacherOptions(), { placeholder: "No class teacher" });
        form.name.value = cls ? cls.name : "";
        form.teacher_id.value = cls && cls.teacher_id ? cls.teacher_id : "";
    });
}

let managedClass = null;

const classSubjectsDialog = formDialog($("#classSubjectsDialog"), async (form) => {
    const subjectId = Number(form.subject_id.value);
    await api(`/api/classes/${managedClass.id}/subjects`, { method: "POST", body: { subject_id: subjectId } });
    toast("Subject added to class.");
    await refreshManagedClass();
    return "keep-open";
});

async function refreshManagedClass() {
    await loadClasses();
    managedClass = state.classes.find((c) => c.id === managedClass.id);
    renderClasses();
    renderClassSubjectChips();
}

function renderClassSubjectChips() {
    const chips = $("#classSubjectChips");
    const select = $("#classSubjectsDialog select");
    const linked = new Set(managedClass.subjects.map((s) => s.id));

    chips.replaceChildren(...(managedClass.subjects.length
        ? managedClass.subjects.map((subject) => el("span", { className: "chip" },
            subject.name,
            el("button", {
                type: "button",
                title: `Remove ${subject.name}`,
                "aria-label": `Remove ${subject.name}`,
                onclick: () => removeClassSubject(subject)
            }, App.icon("x"))
        ))
        : [el("span", { className: "muted", text: "No subjects yet." })]));

    const available = state.subjects.filter((s) => !linked.has(s.id));
    fillSelect(select, available, { placeholder: available.length ? "Choose a subject" : "All subjects already added" });
    select.value = "";
}

async function removeClassSubject(subject) {
    const ok = await confirmAction({
        title: `Remove ${subject.name}?`,
        message: `${subject.name} will no longer be listed for ${managedClass.name}. Existing enrollments and attendance records are not deleted.`,
        confirmLabel: "Remove"
    });

    if (!ok) return;

    try {
        await api(`/api/classes/${managedClass.id}/subjects/${subject.id}`, { method: "DELETE" });
        toast(`Removed ${subject.name} from ${managedClass.name}.`);
        await refreshManagedClass();
    } catch (error) {
        toast(error.message, "error");
    }
}

function openClassSubjects(cls) {
    managedClass = cls;
    classSubjectsDialog.open(() => {
        $("#classSubjectsTitle").textContent = `${cls.name} subjects`;
        renderClassSubjectChips();
    });
}

function renderClasses() {
    const query = $("#classSearch").value;
    const classes = state.classes.filter((c) => matches(c.name, query));

    fillRows($("#classesTable"), 4, classes.map((cls) => [
        el("strong", { text: cls.name }),
        cls.teacher_username ? cls.teacher_username : el("span", { className: "muted", text: "Not assigned" }),
        cls.subjects.length
            ? el("div", { className: "chips" }, ...cls.subjects.map((s) => el("span", { className: "chip", text: s.name })))
            : el("span", { className: "muted", text: "No subjects" }),
        el("td", {}, el("div", { className: "actions" },
            iconButton("list", "Manage subjects", () => openClassSubjects(cls)),
            iconButton("edit", "Edit class", () => openClassDialog(cls))
        ))
    ]), "No classes yet", "Create a class to start organising subjects and students.");
}

async function showClasses(firstVisit) {
    if (firstVisit) {
        $("#classSearch").addEventListener("input", renderClasses);
        $("#newClassButton").addEventListener("click", () => openClassDialog(null));
    }

    stateRow($("#classesTable"), 4, "loading");

    try {
        await Promise.all([loadClasses(), loadSubjects(), loadUsers()]);
        renderClasses();
    } catch (error) {
        stateRow($("#classesTable"), 4, "error", "Could not load classes", error.message);
    }
}

// =====================================================================
// Subjects (FR-08)
// =====================================================================

const subjectDialog = formDialog($("#subjectDialog"), async (form) => {
    const subjectId = form.dataset.subjectId;
    const body = {
        name: form.name.value.trim(),
        teacher_id: form.teacher_id.value ? Number(form.teacher_id.value) : null
    };

    if (subjectId) {
        await api(`/api/subjects/${subjectId}`, { method: "PATCH", body });
        toast(`Updated subject "${body.name}".`);
    } else {
        if (form.class_id.value) body.class_id = Number(form.class_id.value);
        await api("/api/subjects", { method: "POST", body });
        toast(`Created subject "${body.name}".`);
    }

    await loadSubjects();
    renderSubjects();
});

function openSubjectDialog(subject) {
    subjectDialog.open((form) => {
        form.dataset.subjectId = subject ? subject.id : "";
        $("#subjectDialogTitle").textContent = subject ? `Edit ${subject.name}` : "New subject";
        $("#subjectClassField").hidden = Boolean(subject);
        fillSelect(form.teacher_id, teacherOptions(), { placeholder: "No teacher yet" });
        fillSelect(form.class_id, [...state.classes].sort(byName), { placeholder: "None" });
        form.name.value = subject ? subject.name : "";
        form.teacher_id.value = subject && subject.teacher_id ? subject.teacher_id : "";
    });
}

function renderSubjects() {
    const query = $("#subjectSearch").value;
    const subjects = state.subjects.filter((s) => matches(s.name, query));

    fillRows($("#subjectsTable"), 3, subjects.map((subject) => [
        el("strong", { text: subject.name }),
        subject.teacher_username ? subject.teacher_username : el("span", { className: "muted", text: "Not assigned" }),
        el("td", {}, el("div", { className: "actions" },
            iconButton("edit", "Edit subject", () => openSubjectDialog(subject))
        ))
    ]), "No subjects yet", "Create a subject and assign a teacher to it.");
}

async function showSubjects(firstVisit) {
    if (firstVisit) {
        $("#subjectSearch").addEventListener("input", renderSubjects);
        $("#newSubjectButton").addEventListener("click", () => openSubjectDialog(null));
    }

    stateRow($("#subjectsTable"), 3, "loading");

    try {
        await Promise.all([loadSubjects(), loadClasses(), loadUsers()]);
        renderSubjects();
    } catch (error) {
        stateRow($("#subjectsTable"), 3, "error", "Could not load subjects", error.message);
    }
}

// =====================================================================
// Enrollments (FR-09)
// =====================================================================

function updateEnrollSubjects() {
    const select = $("#enrollSubject");
    const hint = $("#enrollSubjectHint");
    const cls = state.classes.find((c) => String(c.id) === $("#enrollClass").value);

    if (!cls) {
        fillSelect(select, [], { placeholder: "Choose a class first" });
        hint.textContent = "Choose a class to see its subjects.";
        return;
    }

    fillSelect(select, cls.subjects, { placeholder: cls.subjects.length ? "Choose a subject" : "No subjects in this class" });
    hint.textContent = cls.subjects.length
        ? `${cls.subjects.length} subject(s) taught in ${cls.name}.`
        : "Add subjects to this class in the Classes page first.";
}

function renderEnrollments() {
    const query = $("#enrollmentSearch").value;
    const classFilter = $("#enrollmentClassFilter").value;

    const rows = state.enrollments.filter((e) =>
        (!classFilter || String(e.class_id) === classFilter)
        && matches(`${e.student_name} ${e.class_name} ${e.subject_name}`, query)
    );

    $("#enrollmentCount").textContent = `${state.enrollments.length} enrollment(s) in total.`;

    fillRows($("#enrollmentsTable"), 4, rows.map((e) => [
        avatarCell(e.student_name),
        e.class_name,
        e.subject_name,
        el("td", {}, el("div", { className: "actions" },
            iconButton("trash", "Remove enrollment", () => removeEnrollment(e))
        ))
    ]), "No enrollments found", "Enroll a student using the form above.");
}

async function removeEnrollment(enrollment) {
    const ok = await confirmAction({
        title: "Remove enrollment?",
        message: `${enrollment.student_name} will be removed from ${enrollment.subject_name} in ${enrollment.class_name}. Past attendance records are kept.`,
        confirmLabel: "Remove"
    });

    if (!ok) return;

    try {
        await api("/api/enrollments", {
            method: "DELETE",
            body: {
                student_id: enrollment.student_id,
                class_id: enrollment.class_id,
                subject_id: enrollment.subject_id
            }
        });
        toast("Enrollment removed.");
        await loadEnrollments();
        renderEnrollments();
    } catch (error) {
        toast(error.message, "error");
    }
}

async function showEnrollments(firstVisit) {
    if (firstVisit) {
        $("#enrollClass").addEventListener("change", updateEnrollSubjects);
        $("#enrollmentSearch").addEventListener("input", renderEnrollments);
        $("#enrollmentClassFilter").addEventListener("input", renderEnrollments);

        $("#enrollForm").addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!event.target.reportValidity()) return;

            try {
                await withLoading($("#enrollButton"), () => api("/api/enrollments", {
                    method: "POST",
                    body: {
                        student_id: Number($("#enrollStudent").value),
                        class_id: Number($("#enrollClass").value),
                        subject_id: Number($("#enrollSubject").value)
                    }
                }));
                toast("Student enrolled.");
                $("#enrollStudent").value = "";
                await loadEnrollments();
                renderEnrollments();
            } catch (error) {
                toast(error.message, "error");
            }
        });
    }

    stateRow($("#enrollmentsTable"), 4, "loading");

    try {
        await Promise.all([loadUsers(), loadClasses(), loadEnrollments()]);

        const students = state.users
            .filter((u) => u.role === "student" && u.active)
            .map((u) => ({ id: u.id, name: u.username }));
        const classes = [...state.classes].sort(byName);

        fillSelect($("#enrollStudent"), students, { placeholder: students.length ? "Choose a student" : "No active students" });
        fillSelect($("#enrollClass"), classes, { placeholder: classes.length ? "Choose a class" : "No classes yet" });
        fillSelect($("#enrollmentClassFilter"), classes, { placeholder: "All classes" });
        updateEnrollSubjects();
        renderEnrollments();
    } catch (error) {
        stateRow($("#enrollmentsTable"), 4, "error", "Could not load enrollments", error.message);
    }
}

// =====================================================================
// Attendance reports (FR-04 / FR-05)
// =====================================================================

let percentRows = [];

function renderPercentages() {
    const query = $("#percentSearch").value;
    const rows = percentRows.filter((s) => matches(s.student_name, query));

    fillRows($("#percentTable"), 4, rows.map((s) => [
        avatarCell(s.student_name),
        el("td", { className: "num", text: s.classes_attended }),
        el("td", { className: "num", text: s.total_classes }),
        progress(s.attendance_percentage, s.total_classes > 0)
    ]), "No students found", "Create student accounts to see percentages.");
}

async function loadPercentages() {
    const subjectId = $("#percentSubject").value;
    stateRow($("#percentTable"), 4, "loading");

    try {
        const url = subjectId ? `/api/attendance/percentages?subject_id=${subjectId}` : "/api/attendance/percentages";
        percentRows = (await api(url)).students;
        renderPercentages();
    } catch (error) {
        stateRow($("#percentTable"), 4, "error", "Could not load percentages", error.message);
    }
}

async function loadRecords() {
    const params = new URLSearchParams();
    if ($("#recordSubject").value) params.set("subject_id", $("#recordSubject").value);
    if ($("#recordDate").value) params.set("attendance_date", $("#recordDate").value);
    if ($("#recordStatus").value) params.set("status", $("#recordStatus").value);

    stateRow($("#recordsTable"), 4, "loading");

    try {
        const { records } = await api(`/api/attendance?${params}`);
        $("#recordCount").textContent = `${records.length} record(s) match the current filters.`;
        fillRows($("#recordsTable"), 4, records.map((r) => [
            formatDate(r.attendance_date),
            avatarCell(r.student_name),
            r.subject_name,
            App.statusBadge(r.status)
        ]), "No attendance records", "Records appear here once teachers mark attendance.");
    } catch (error) {
        stateRow($("#recordsTable"), 4, "error", "Could not load records", error.message);
    }
}

async function showAttendance(firstVisit) {
    if (firstVisit) {
        $("#percentSearch").addEventListener("input", renderPercentages);
        $("#percentSubject").addEventListener("change", loadPercentages);
        ["#recordSubject", "#recordDate", "#recordStatus"].forEach((id) =>
            $(id).addEventListener("change", loadRecords)
        );
        $("#recordClear").addEventListener("click", () => {
            $("#recordSubject").value = "";
            $("#recordDate").value = "";
            $("#recordStatus").value = "";
            loadRecords();
        });
    }

    try {
        await loadSubjects();
        fillSelect($("#percentSubject"), state.subjects, { placeholder: "All subjects" });
        fillSelect($("#recordSubject"), state.subjects, { placeholder: "All subjects" });
    } catch (error) {
        toast(error.message, "error");
    }

    loadPercentages();
    loadRecords();
}

// =====================================================================
// Start-up
// =====================================================================

const sections = {
    overview: { title: "Overview", subtitle: "A summary of users, classes and attendance.", show: showOverview },
    users: { title: "Users", subtitle: "Manage administrator, teacher and student accounts.", show: showUsers },
    classes: { title: "Classes", subtitle: "Create classes and choose the subjects they include.", show: showClasses },
    subjects: { title: "Subjects", subtitle: "Create subjects and assign their teachers.", show: showSubjects },
    enrollments: { title: "Enrollments", subtitle: "Enroll students into class subjects.", show: showEnrollments },
    attendance: { title: "Attendance", subtitle: "Attendance percentages and records across all subjects.", show: showAttendance }
};

// Quick-action links on the overview open the matching "new" dialog.
document.querySelectorAll("[data-action]").forEach((link) => {
    link.addEventListener("click", () => {
        const action = link.dataset.action;
        setTimeout(() => {
            if (action === "new-user") openUserDialog(null);
            if (action === "new-class") openClassDialog(null);
            if (action === "new-subject") openSubjectDialog(null);
        }, 300);
    });
});

(async () => {
    try {
        state.me = (await api("/api/me")).user;
    } catch (error) {
        toast(error.message, "error");
        return;
    }

    App.initSections(sections, (name, firstVisit) => sections[name].show(firstVisit));
})();
