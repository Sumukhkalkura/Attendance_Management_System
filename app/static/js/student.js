/* Student dashboard: personal attendance overview and history (FR-05).
   The backend only returns the logged-in student's own records. */

"use strict";

const { api, el, $, statusBadge, progress, percentTone, formatPercent, formatDate,
    stateBlock, stateRow, fillRows, fillSelect } = App;

const RING_CIRCUMFERENCE = 2 * Math.PI * 52;

let records = [];
let recordsLoaded = null;

// Present divided by all marked classes, rounded to two decimals like FR-04.
function percentOf(list) {
    const present = list.filter((r) => r.status === "Present").length;
    return list.length ? Math.round((present / list.length) * 10000) / 100 : 0;
}

function loadRecords() {
    if (!recordsLoaded) {
        recordsLoaded = api("/api/attendance").then((data) => { records = data.records; });
        recordsLoaded.catch(() => { recordsLoaded = null; });
    }
    return recordsLoaded;
}

function subjectsInRecords() {
    const map = new Map();
    for (const r of records) {
        if (!map.has(r.subject_id)) map.set(r.subject_id, { id: r.subject_id, name: r.subject_name, records: [] });
        map.get(r.subject_id).records.push(r);
    }
    return [...map.values()].sort((a, b) => a.name.localeCompare(b.name));
}

// =====================================================================
// Overview
// =====================================================================

function renderRing(percent, hasData) {
    const ring = $("#ringValue");
    ring.setAttribute("class", `ring-value ${hasData ? percentTone(percent) : ""}`);
    requestAnimationFrame(() => {
        ring.setAttribute("stroke-dashoffset", String(RING_CIRCUMFERENCE * (1 - (hasData ? percent : 0) / 100)));
    });
    $("#overallPercent").textContent = hasData ? formatPercent(percent) : "–";
}

async function showOverview() {
    const breakdown = $("#subjectBreakdown");
    const recent = $("#recentList");
    breakdown.replaceChildren(stateBlock("loading"));
    recent.replaceChildren(stateBlock("loading"));

    try {
        await loadRecords();
    } catch (error) {
        $("#overallHeadline").textContent = "Could not load your attendance";
        $("#overallMessage").textContent = error.message;
        breakdown.replaceChildren(stateBlock("error", "Could not load attendance", error.message));
        recent.replaceChildren();
        return;
    }

    const count = (status) => records.filter((r) => r.status === status).length;
    const percent = percentOf(records);
    const hasData = records.length > 0;

    renderRing(percent, hasData);
    $("#countPresent").textContent = count("Present");
    $("#countAbsent").textContent = count("Absent");
    $("#countLate").textContent = count("Late");
    $("#countTotal").textContent = records.length;

    if (!hasData) {
        $("#overallHeadline").textContent = "No attendance recorded yet";
        $("#overallMessage").textContent = "Your attendance will appear here once your teachers start marking classes.";
    } else if (percent >= 75) {
        $("#overallHeadline").textContent = "You're on track";
        $("#overallMessage").textContent = "Your overall attendance meets the 75% requirement. Keep it up!";
    } else {
        $("#overallHeadline").textContent = "Your attendance needs attention";
        $("#overallMessage").textContent = "Your overall attendance is below 75%. Try not to miss upcoming classes.";
    }

    const subjects = subjectsInRecords();
    breakdown.replaceChildren(...(subjects.length
        ? subjects.map((subject) => {
            const present = subject.records.filter((r) => r.status === "Present").length;
            return el("div", {},
                el("div", { className: "subject-row-head" },
                    el("strong", { text: subject.name }),
                    el("span", { text: `${present} of ${subject.records.length} classes attended` })
                ),
                progress(percentOf(subject.records))
            );
        })
        : [stateBlock("empty", "No subjects yet", "Subjects appear once attendance is recorded.")]));

    const latest = records.slice(0, 6);
    recent.replaceChildren(...(latest.length
        ? latest.map((r) => el("li", {},
            el("div", {},
                el("div", { text: r.subject_name }),
                el("div", { className: "muted", text: formatDate(r.attendance_date) })
            ),
            statusBadge(r.status)
        ))
        : [stateBlock("empty", "Nothing yet")]));
}

// =====================================================================
// History
// =====================================================================

function renderHistory() {
    const subject = $("#historySubject").value;
    const status = $("#historyStatus").value;
    const date = $("#historyDate").value;

    const rows = records.filter((r) =>
        (!subject || String(r.subject_id) === subject)
        && (!status || r.status === status)
        && (!date || r.attendance_date === date)
    );

    $("#historyCount").textContent = `${rows.length} of ${records.length} record(s) shown.`;

    fillRows($("#historyTable"), 3, rows.map((r) => [
        formatDate(r.attendance_date),
        r.subject_name,
        statusBadge(r.status)
    ]), "No matching records", records.length ? "Try different filters." : "No attendance has been recorded for you yet.");
}

async function showHistory(firstVisit) {
    if (firstVisit) {
        ["#historySubject", "#historyStatus", "#historyDate"].forEach((id) =>
            $(id).addEventListener("change", renderHistory)
        );
    }

    stateRow($("#historyTable"), 3, "loading");

    try {
        await loadRecords();
        fillSelect($("#historySubject"), subjectsInRecords(), { placeholder: "All subjects" });
        renderHistory();
    } catch (error) {
        stateRow($("#historyTable"), 3, "error", "Could not load attendance", error.message);
    }
}

// =====================================================================
// Start-up
// =====================================================================

const sections = {
    overview: { title: "My attendance", subtitle: "Your overall and subject-wise attendance.", show: showOverview },
    history: { title: "Attendance history", subtitle: "Every class you have been marked for.", show: showHistory }
};

App.initSections(sections, (name, firstVisit) => sections[name].show(firstVisit));
