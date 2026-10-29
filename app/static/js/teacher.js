/* Teacher dashboard: overview, attendance marking (FR-02), record
   corrections (FR-03), viewing (FR-05) and percentages (FR-04). */

"use strict";

const { api, el, $, iconButton, avatarCell, statusBadge, progress, formatDate, todayIso,
    stateRow, fillRows, fillSelect, toast, withLoading, confirmAction, formDialog } = App;

const STATUSES = ["Present", "Absent", "Late"];

const state = {
    subjects: [],
    classes: [],
    roster: null,
    records: []
};

async function loadAssignments() {
    const [subjects, classes] = await Promise.all([
        api("/api/teacher/subjects"),
        api("/api/teacher/classes")
    ]);
    state.subjects = subjects.subjects;
    state.classes = classes.classes;
}

function subjectFilterOptions(select) {
    fillSelect(select, state.subjects, { placeholder: "All my subjects" });
}

function matches(text, query) {
    return text.toLowerCase().includes(query.trim().toLowerCase());
}

// =====================================================================
// Overview
// =====================================================================

async function showOverview() {
    const list = $("#subjectList");
    const lowTable = $("#lowTable");
    list.replaceChildren(App.stateBlock("loading"));
    stateRow(lowTable, 2, "loading");

    try {
        const [, percentages] = await Promise.all([loadAssignments(), api("/api/attendance/percentages")]);

        // Only students with records in this teacher's subjects are relevant.
        const tracked = percentages.students.filter((s) => s.total_classes > 0);
        const attended = tracked.reduce((sum, s) => sum + s.classes_attended, 0);
        const total = tracked.reduce((sum, s) => sum + s.total_classes, 0);

        $("#statSubjects").textContent = state.subjects.length;
        $("#statClasses").textContent = state.classes.length;
        $("#statStudents").textContent = tracked.length;
        $("#statAverage").textContent = total ? App.formatPercent(Math.round(attended / total * 1000) / 10) : "–";
        $("#statAverageSub").textContent = total ? `${attended} of ${total} marked classes` : "No attendance marked yet";

        list.replaceChildren(...(state.subjects.length
            ? state.subjects.map((s) => el("li", {}, el("strong", { text: s.name }), App.badge("Assigned", "blue")))
            : [App.stateBlock("empty", "No subjects assigned", "Ask an administrator to assign you a subject.")]));

        const low = tracked
            .filter((s) => s.attendance_percentage < 75)
            .sort((a, b) => a.attendance_percentage - b.attendance_percentage)
            .slice(0, 6);

        fillRows(lowTable, 2, low.map((s) => [avatarCell(s.student_name), progress(s.attendance_percentage)]),
            "Everyone is on track", "No student is below 75% in your subjects.");

    } catch (error) {
        list.replaceChildren(App.stateBlock("error", "Could not load overview", error.message));
        stateRow(lowTable, 2, "error", "Could not load overview", error.message);
    }
}

// =====================================================================
// Mark attendance (FR-02)
// =====================================================================

function updateCounts() {
    const counts = { Present: 0, Absent: 0, Late: 0 };
    document.querySelectorAll("#rosterTable input[type=radio]:checked").forEach((input) => {
        counts[input.value] += 1;
    });
    $("#countPresent").textContent = counts.Present;
    $("#countAbsent").textContent = counts.Absent;
    $("#countLate").textContent = counts.Late;
}

function statusControl(student) {
    const name = `status-${student.student_id}`;
    const current = student.status || "Present";

    return el("div", { className: "segmented", role: "radiogroup", "aria-label": `Status for ${student.username}` },
        ...STATUSES.map((status) => el("label", { className: `seg-${status.toLowerCase()}` },
            el("input", {
                type: "radio",
                name,
                value: status,
                checked: status === current,
                dataset: { studentId: student.student_id },
                onchange: updateCounts
            }),
            el("span", { text: status })
        ))
    );
}

function renderRoster() {
    const roster = state.roster;
    const saved = roster.students.filter((s) => s.status).length;

    $("#rosterCard").hidden = false;
    $("#rosterTitle").textContent = `${roster.class_name} · ${roster.subject_name}`;
    $("#rosterSubtitle").textContent = `${formatDate(roster.attendance_date)} · ${roster.count} student(s) · `
        + (saved ? `${saved} already saved, changes will update them` : "not marked yet");

    const hasStudents = roster.students.length > 0;
    $("#markSummary").hidden = !hasStudents;
    $("#allPresent").disabled = !hasStudents;
    $("#allAbsent").disabled = !hasStudents;

    fillRows($("#rosterTable"), 3, roster.students.map((student) => [
        avatarCell(student.username),
        student.status ? statusBadge(student.status) : el("span", { className: "muted", text: "Not marked" }),
        statusControl(student)
    ]), "No students enrolled", "No students are enrolled in this class for this subject.");

    updateCounts();
}

async function loadRoster() {
    const classId = $("#markClass").value;
    const subjectId = $("#markSubject").value;
    const date = $("#markDate").value;

    $("#rosterCard").hidden = false;
    stateRow($("#rosterTable"), 3, "loading");

    try {
        const params = new URLSearchParams({ class_id: classId, subject_id: subjectId, attendance_date: date });
        state.roster = await api(`/api/roster?${params}`);
        renderRoster();
    } catch (error) {
        $("#markSummary").hidden = true;
        stateRow($("#rosterTable"), 3, "error", "Could not load roster", error.message);
    }
}

function setAll(status) {
    document.querySelectorAll(`#rosterTable input[value="${status}"]`).forEach((input) => {
        input.checked = true;
    });
    updateCounts();
}

async function saveAttendance() {
    const roster = state.roster;
    const records = [...document.querySelectorAll("#rosterTable input[type=radio]:checked")].map((input) => ({
        student_id: Number(input.dataset.studentId),
        status: input.value
    }));

    try {
        // Batch submission: every enrolled student must be included; existing
        // records for this date are updated rather than rejected.
        const result = await withLoading($("#saveAttendance"), () => api("/api/attendance", {
            method: "POST",
            body: {
                class_id: roster.class_id,
                subject_id: roster.subject_id,
                attendance_date: roster.attendance_date,
                update_existing: true,
                records
            }
        }));
        toast(`Saved attendance for ${result.count} student(s).`);
        await loadRoster();
    } catch (error) {
        toast(error.message, "error");
    }
}

async function showMark(firstVisit) {
    if (firstVisit) {
        $("#markDate").value = todayIso();
        $("#markDate").max = todayIso();
        $("#rosterForm").addEventListener("submit", (event) => {
            event.preventDefault();
            if (event.target.reportValidity()) {
                withLoading($("#loadRosterButton"), loadRoster);
            }
        });
        $("#allPresent").addEventListener("click", () => setAll("Present"));
        $("#allAbsent").addEventListener("click", () => setAll("Absent"));
        $("#saveAttendance").addEventListener("click", saveAttendance);
    }

    try {
        await loadAssignments();
        fillSelect($("#markClass"), state.classes, { placeholder: state.classes.length ? "Choose a class" : "No classes with your students" });
        fillSelect($("#markSubject"), state.subjects, { placeholder: state.subjects.length ? "Choose a subject" : "No subjects assigned" });
    } catch (error) {
        toast(error.message, "error");
    }
}

// =====================================================================
// Records: view, correct, delete (FR-03 / FR-05)
// =====================================================================

const editDialog = formDialog($("#editRecordDialog"), async (form) => {
    const recordId = form.dataset.recordId;
    await api(`/api/attendance/${recordId}`, { method: "PATCH", body: { status: form.status.value } });
    toast("Attendance record updated.");
    await loadRecords();
});

function openEdit(record) {
    editDialog.open((form) => {
        form.dataset.recordId = record.id;
        form.status.value = record.status;
        $("#editRecordSummary").textContent =
            `${record.student_name} · ${record.subject_name} · ${formatDate(record.attendance_date)}`;
    });
}

async function deleteRecord(record) {
    const ok = await confirmAction({
        title: "Delete this record?",
        message: `${record.student_name}'s ${record.status} record for ${record.subject_name} on ${formatDate(record.attendance_date)} will be permanently deleted.`,
        confirmLabel: "Delete"
    });

    if (!ok) return;

    try {
        await api(`/api/attendance/${record.id}`, { method: "DELETE" });
        toast("Attendance record deleted.");
        await loadRecords();
    } catch (error) {
        toast(error.message, "error");
    }
}

function renderRecords() {
    const query = $("#recordSearch").value;
    const rows = state.records.filter((r) => matches(r.student_name, query));

    $("#recordCount").textContent = `${rows.length} record(s). Correct a status or delete a record entered by mistake.`;

    fillRows($("#recordsTable"), 5, rows.map((record) => [
        formatDate(record.attendance_date),
        avatarCell(record.student_name),
        record.subject_name,
        statusBadge(record.status),
        el("td", {}, el("div", { className: "actions" },
            iconButton("edit", "Correct status", () => openEdit(record)),
            iconButton("trash", "Delete record", () => deleteRecord(record))
        ))
    ]), "No attendance records", "Records appear here after you mark attendance.");
}

async function loadRecords() {
    const params = new URLSearchParams();
    if ($("#recordSubject").value) params.set("subject_id", $("#recordSubject").value);
    if ($("#recordDate").value) params.set("attendance_date", $("#recordDate").value);
    if ($("#recordStatus").value) params.set("status", $("#recordStatus").value);

    stateRow($("#recordsTable"), 5, "loading");

    try {
        state.records = (await api(`/api/attendance?${params}`)).records;
        renderRecords();
    } catch (error) {
        stateRow($("#recordsTable"), 5, "error", "Could not load records", error.message);
    }
}

async function showRecords(firstVisit) {
    if (firstVisit) {
        $("#recordSearch").addEventListener("input", renderRecords);
        ["#recordSubject", "#recordDate", "#recordStatus"].forEach((id) =>
            $(id).addEventListener("change", loadRecords)
        );
    }

    try {
        await loadAssignments();
        subjectFilterOptions($("#recordSubject"));
    } catch (error) {
        toast(error.message, "error");
    }

    loadRecords();
}

// =====================================================================
// Percentages (FR-04)
// =====================================================================

let percentRows = [];

function renderPercentages() {
    const query = $("#percentSearch").value;
    // Students without records in this teacher's subjects are not shown.
    const rows = percentRows.filter((s) => s.total_classes > 0 && matches(s.student_name, query));

    fillRows($("#percentTable"), 4, rows.map((s) => [
        avatarCell(s.student_name),
        el("td", { className: "num", text: s.classes_attended }),
        el("td", { className: "num", text: s.total_classes }),
        progress(s.attendance_percentage)
    ]), "No attendance yet", "Percentages appear once attendance has been marked.");
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

async function showPercentages(firstVisit) {
    if (firstVisit) {
        $("#percentSearch").addEventListener("input", renderPercentages);
        $("#percentSubject").addEventListener("change", loadPercentages);
    }

    try {
        await loadAssignments();
        subjectFilterOptions($("#percentSubject"));
    } catch (error) {
        toast(error.message, "error");
    }

    loadPercentages();
}

// =====================================================================
// Start-up
// =====================================================================

const sections = {
    overview: { title: "Overview", subtitle: "Your subjects, classes and attendance at a glance.", show: showOverview },
    mark: { title: "Mark attendance", subtitle: "Record Present, Absent or Late for a class session.", show: showMark },
    records: { title: "Attendance records", subtitle: "Review and correct attendance in your subjects.", show: showRecords },
    percentages: { title: "Percentages", subtitle: "Attendance percentages for students in your subjects.", show: showPercentages }
};

App.initSections(sections, (name, firstVisit) => sections[name].show(firstVisit));
