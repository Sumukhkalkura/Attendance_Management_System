/* Reports and export screen shared by the administrator and teacher
   dashboards (FR-06 reporting, FR-12 export).

   Uses the existing API only:
     GET /api/reports/attendance?student_id&class_id&subject_id&start_date&end_date&status
     GET /api/reports/attendance/export/<csv|pdf|json>?<same filters>
   The server applies the role rules (teachers: own subjects; admins: all). */

"use strict";

const Reports = (() => {
    const { api, el, $, avatarCell, statusBadge, formatDate, formatPercent, stateRow, fillRows, fillSelect,
        toast, withLoading } = App;

    const FILTERS = [
        ["#reportStudent", "student_id"],
        ["#reportClass", "class_id"],
        ["#reportSubject", "subject_id"],
        ["#reportFrom", "start_date"],
        ["#reportTo", "end_date"],
        ["#reportStatus", "status"]
    ];

    let loadOptions = null;
    let lastReport = null;      // { params, count } of the report on screen

    function currentParams() {
        const params = new URLSearchParams();
        FILTERS.forEach(([selector, name]) => {
            const value = $(selector).value;
            if (value) params.set(name, value);
        });
        return params;
    }

    function selectedText(selector) {
        const select = $(selector);
        return select.value ? select.options[select.selectedIndex].text : "";
    }

    function describe(params) {
        const parts = [];
        if (params.get("student_id")) parts.push(`student ${selectedText("#reportStudent")}`);
        if (params.get("class_id")) parts.push(`class ${selectedText("#reportClass")}`);
        if (params.get("subject_id")) parts.push(`subject ${selectedText("#reportSubject")}`);
        if (params.get("start_date") || params.get("end_date")) {
            const from = params.get("start_date") ? formatDate(params.get("start_date")) : "the first record";
            const to = params.get("end_date") ? formatDate(params.get("end_date")) : "the latest record";
            parts.push(`from ${from} to ${to}`);
        }
        if (params.get("status")) parts.push(`status ${params.get("status")}`);
        return parts.length ? `Filters: ${parts.join("; ")}.` : "Filters: none (all attendance you may view).";
    }

    function showError(message) {
        $("#reportError").textContent = message || "";
    }

    function render(report, params) {
        const summary = report.summary || {};
        $("#reportResult").hidden = false;
        $("#reportScope").textContent = describe(params);
        $("#reportTotal").textContent = summary.total_records ?? report.count ?? 0;
        $("#reportPresent").textContent = summary.present_count ?? 0;
        $("#reportAbsent").textContent = summary.absent_count ?? 0;
        $("#reportLate").textContent = summary.late_count ?? 0;
        $("#reportPercent").textContent = summary.total_records ? formatPercent(summary.attendance_percentage) : "-";

        fillRows($("#reportTable"), 5, (report.records || []).map((r) => [
            formatDate(r.attendance_date),
            avatarCell(r.student_name),
            r.class_name || el("span", { className: "muted", text: "-" }),
            r.subject_name,
            statusBadge(r.status)
        ]), "No attendance records match this report",
        "There is nothing to report for these filters. Try a wider date range or fewer filters.");
    }

    async function generate() {
        showError("");
        const params = currentParams();
        const from = params.get("start_date");
        const to = params.get("end_date");
        if (from && to && from > to) {
            showError("The From date must be on or before the To date.");
            return;
        }

        $("#reportResult").hidden = false;
        stateRow($("#reportTable"), 5, "loading");
        try {
            const report = await withLoading($("#reportGenerate"), () => api(`/api/reports/attendance?${params}`));
            lastReport = { params, count: report.count ?? (report.records || []).length };
            render(report, params);
        } catch (error) {
            lastReport = null;
            $("#reportResult").hidden = true;
            showError(error.message);
            toast(error.message, "error");
        }
    }

    function filenameFrom(response, fallback) {
        const header = response.headers.get("Content-Disposition") || "";
        const match = header.match(/filename="?([^";]+)"?/i);
        return match ? match[1] : fallback;
    }

    async function exportReport(button) {
        const format = button.dataset.format;
        if (!lastReport) {
            toast("Generate a report before exporting it.", "error");
            return;
        }
        if (lastReport.count === 0) {
            toast("This report has no records, so there is nothing to export.", "error");
            return;
        }

        try {
            await withLoading(button, async () => {
                let response;
                try {
                    response = await fetch(`/api/reports/attendance/export/${format}?${lastReport.params}`,
                        { credentials: "same-origin" });
                } catch (networkError) {
                    throw new Error("Unable to reach the server. Check that Flask is running.");
                }
                if (response.status === 401) {
                    window.location.href = "/login";
                    throw new Error("Your session has expired. Please sign in again.");
                }
                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.error || `Export failed (${response.status})`);
                }

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const link = el("a", { href: url, download: filenameFrom(response, `attendance_report.${format}`) });
                document.body.append(link);
                link.click();
                link.remove();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            });
            toast(`Report exported as ${format.toUpperCase()}.`);
        } catch (error) {
            toast(error.message, "error");
        }
    }

    function reset() {
        FILTERS.forEach(([selector]) => { $(selector).value = ""; });
        showError("");
        lastReport = null;
        $("#reportResult").hidden = true;
    }

    async function show(firstVisit) {
        if (firstVisit) {
            $("#reportForm").addEventListener("submit", (event) => {
                event.preventDefault();
                generate();
            });
            $("#reportReset").addEventListener("click", reset);
            ["#reportExportCsv", "#reportExportPdf", "#reportExportJson"].forEach((id) =>
                $(id).addEventListener("click", (event) => exportReport(event.currentTarget))
            );
        }

        try {
            const options = await loadOptions();
            fillSelect($("#reportStudent"), options.students, { placeholder: "All students" });
            fillSelect($("#reportClass"), options.classes, { placeholder: "All classes" });
            fillSelect($("#reportSubject"), options.subjects, { placeholder: "All subjects" });
        } catch (error) {
            showError(error.message);
        }
    }

    function setup(options) {
        loadOptions = options.loadOptions;
        return { title: "Reports", subtitle: options.subtitle, show };
    }

    return { setup };
})();
