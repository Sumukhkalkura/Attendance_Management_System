"""FR-06 / FR-12 reusable report export helpers: CSV and PDF generation,
filename building, CSV injection protection, and response formatting.

Contains no routes.
"""

import csv
import io
import textwrap
from datetime import datetime

from flask import jsonify, Response


# =====================================================================
# FR-06 & FR-12: Attendance Reporting & Export Helpers
# =====================================================================

SUPPORTED_EXPORT_FORMATS = {"csv", "pdf", "json"}


def _get_export_filename(report_payload, file_ext):
    """Determine a sensible download filename based on applied filters."""
    if report_payload.get("student"):
        username = report_payload["student"].get("username", "student")
        return f"attendance_report_student_{username}.{file_ext}"
    if report_payload.get("class"):
        cname = str(report_payload["class"].get("name", "class")).replace(" ", "_")
        return f"attendance_report_class_{cname}.{file_ext}"
    if report_payload.get("subject"):
        sname = str(report_payload["subject"].get("name", "subject")).replace(" ", "_")
        return f"attendance_report_subject_{sname}.{file_ext}"
    return f"attendance_report.{file_ext}"


def _sanitize_csv_cell(value):
    """Sanitize cell value to prevent CSV Formula Injection (CWE-1236).

    Prepend a single quote (') if the text begins with '=', '+', '-', '@', '\t', or '\r',
    or begins with whitespace followed by one of those formula triggers.
    """
    if value is None:
        return ""
    val_str = str(value)
    stripped = val_str.lstrip(" \t\r\n")
    if val_str and (val_str[0] in ("=", "+", "-", "@", "\t", "\r") or (stripped and stripped[0] in ("=", "+", "-", "@"))):
        return f"'{val_str}"
    return val_str


def _generate_csv_report(report_payload):
    """Generate a clean, RFC 4180 compliant CSV string for the attendance report."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Attendance ID",
        "Date",
        "Student ID",
        "Student Name",
        "Class ID",
        "Class Name",
        "Subject ID",
        "Subject Name",
        "Status",
    ])

    for rec in report_payload.get("records", []):
        writer.writerow([
            _sanitize_csv_cell(rec.get("attendance_id") or rec.get("id")),
            _sanitize_csv_cell(rec.get("attendance_date") or rec.get("date")),
            _sanitize_csv_cell(rec.get("student_id")),
            _sanitize_csv_cell(rec.get("student_name") or rec.get("student_username")),
            _sanitize_csv_cell(rec.get("class_id") or ""),
            _sanitize_csv_cell(rec.get("class_name") or ""),
            _sanitize_csv_cell(rec.get("subject_id") or ""),
            _sanitize_csv_cell(rec.get("subject_name") or ""),
            _sanitize_csv_cell(rec.get("status")),
        ])

    return output.getvalue()


def _generate_pdf_report(report_payload, title="Attendance Report"):
    """Generate a clean, valid PDF 1.4 document for the attendance report.

    Formats text properly without truncating or overlapping long student names,
    subject names, or class names, and paginates large reports cleanly.
    """
    summary = report_payload.get("summary", {})
    filters = report_payload.get("filters", {})
    records = report_payload.get("records", [])

    w_date = 12
    w_student = 20
    w_class = 14
    w_subject = 22
    w_status = 10
    table_width = 82
    table_sep = "-" * table_width
    table_header = f"{'Date':<12} {'Student':<20} {'Class':<14} {'Subject':<22} {'Status':<10}"

    meta_lines = []
    meta_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    filter_parts = []
    if report_payload.get("student"):
        filter_parts.append(
            f"Student: {report_payload['student'].get('username', '')} (ID: {report_payload['student'].get('id', '')})"
        )
    elif filters.get("student_id"):
        filter_parts.append(f"Student ID: {filters['student_id']}")

    if report_payload.get("class"):
        filter_parts.append(
            f"Class: {report_payload['class'].get('name', '')} (ID: {report_payload['class'].get('id', '')})"
        )
    elif filters.get("class_id"):
        filter_parts.append(f"Class ID: {filters['class_id']}")

    if report_payload.get("subject"):
        filter_parts.append(
            f"Subject: {report_payload['subject'].get('name', '')} (ID: {report_payload['subject'].get('id', '')})"
        )
    elif filters.get("subject_id"):
        filter_parts.append(f"Subject ID: {filters['subject_id']}")

    if filters.get("start_date") or filters.get("end_date"):
        start = filters.get("start_date") or "Earliest"
        end = filters.get("end_date") or "Latest"
        filter_parts.append(f"Date Range: {start} to {end}")

    if filters.get("status"):
        filter_parts.append(f"Status Filter: {filters['status']}")

    filter_text = "Filters: " + (" | ".join(filter_parts) if filter_parts else "All Records")
    for f_line in textwrap.wrap(filter_text, width=table_width):
        meta_lines.append(f_line)

    summary_text = (
        f"Summary: Total: {summary.get('total_records', len(records))} | "
        f"Present: {summary.get('present_count', 0)} | "
        f"Absent: {summary.get('absent_count', 0)} | "
        f"Late: {summary.get('late_count', 0)} | "
        f"Attendance Rate: {summary.get('attendance_percentage', 0.0)}%"
    )
    for s_line in textwrap.wrap(summary_text, width=table_width):
        meta_lines.append(s_line)

    MAX_PAGE_LINES = 38
    pages = []
    current_page = list(meta_lines)
    current_page.append(table_sep)
    current_page.append(table_header)
    current_page.append(table_sep)

    def start_new_page():
        nonlocal current_page
        pages.append(current_page)
        current_page = [table_sep, table_header, table_sep]

    if not records:
        current_page.append("No attendance records found matching the specified criteria.")
        current_page.append(table_sep)
        current_page.append("End of Attendance Report")
        pages.append(current_page)
    else:
        for r in records:
            r_date = str(r.get("attendance_date") or r.get("date") or "")
            r_student = str(r.get("student_name") or r.get("student_username") or "")
            r_class = str(r.get("class_name") or "N/A")
            r_subject = str(r.get("subject_name") or "")
            r_status = str(r.get("status") or "")

            d_lines = textwrap.wrap(r_date, width=w_date, break_long_words=True) or [""]
            st_lines = textwrap.wrap(r_student, width=w_student, break_long_words=True) or [""]
            c_lines = textwrap.wrap(r_class, width=w_class, break_long_words=True) or [""]
            su_lines = textwrap.wrap(r_subject, width=w_subject, break_long_words=True) or [""]
            stat_lines = textwrap.wrap(r_status, width=w_status, break_long_words=True) or [""]

            row_height = max(len(d_lines), len(st_lines), len(c_lines), len(su_lines), len(stat_lines))
            row_lines = []
            for i in range(row_height):
                d = d_lines[i] if i < len(d_lines) else ""
                st = st_lines[i] if i < len(st_lines) else ""
                c = c_lines[i] if i < len(c_lines) else ""
                su = su_lines[i] if i < len(su_lines) else ""
                stat = stat_lines[i] if i < len(stat_lines) else ""
                row_lines.append(f"{d:<12} {st:<20} {c:<14} {su:<22} {stat:<10}".rstrip())

            if len(current_page) + row_height > MAX_PAGE_LINES and len(current_page) > 3:
                start_new_page()

            current_page.extend(row_lines)

        if len(current_page) + 2 > MAX_PAGE_LINES and len(current_page) > 3:
            start_new_page()
        current_page.append(table_sep)
        current_page.append("End of Attendance Report")
        pages.append(current_page)

    num_pages = len(pages)
    font_obj_num = 3
    page_obj_nums = [4 + 2 * i for i in range(num_pages)]
    content_obj_nums = [5 + 2 * i for i in range(num_pages)]
    total_objects = 3 + 2 * num_pages

    obj_dict = {}
    obj_dict[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids_str = " ".join(f"{num} 0 R" for num in page_obj_nums)
    obj_dict[2] = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>".encode("ascii")
    obj_dict[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"

    for i, p_lines in enumerate(pages):
        page_num = i + 1
        stream_cmds = ["BT", "/F1 12 Tf", "40 750 Td"]
        page_title = title if num_pages == 1 else f"{title} (Page {page_num} of {num_pages})"
        escaped_title = page_title.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_cmds.append(f"({escaped_title}) Tj")
        stream_cmds.append("/F1 9 Tf")
        stream_cmds.append("0 -20 Td")

        for line_item in p_lines:
            escaped = line_item.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_cmds.append(f"({escaped}) Tj")
            stream_cmds.append("0 -14 Td")
        stream_cmds.append("ET")
        stream_bytes = "\n".join(stream_cmds).encode("latin1", errors="replace")

        p_obj = page_obj_nums[i]
        c_obj = content_obj_nums[i]
        obj_dict[p_obj] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {c_obj} 0 R /Resources << /Font << /F1 {font_obj_num} 0 R >> >> >>"
        ).encode("ascii")
        obj_dict[c_obj] = (
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream"
        )

    out = [b"%PDF-1.4\n"]
    offsets = {}
    for obj_num in range(1, total_objects + 1):
        offsets[obj_num] = sum(len(x) for x in out)
        out.append(f"{obj_num} 0 obj\n".encode("ascii") + obj_dict[obj_num] + b"\nendobj\n")

    xref_offset = sum(len(x) for x in out)
    out.append(f"xref\n0 {total_objects + 1}\n0000000000 65535 f \n".encode("ascii"))
    for obj_num in range(1, total_objects + 1):
        out.append(f"{offsets[obj_num]:010d} 00000 n \n".encode("ascii"))
    out.append(
        f"trailer\n<< /Size {total_objects + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return b"".join(out)


def _format_export_response(report_payload, fmt):
    """Format and return the HTTP Response for the requested export format."""
    clean_fmt = fmt.lower().strip() if isinstance(fmt, str) else ""
    if clean_fmt not in SUPPORTED_EXPORT_FORMATS:
        return jsonify(
            error=f"Unsupported export format '{clean_fmt}'. Supported formats are: csv, pdf, json"
        ), 400

    if clean_fmt == "csv":
        csv_data = _generate_csv_report(report_payload)
        filename = _get_export_filename(report_payload, "csv")
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            status=200,
        )

    elif clean_fmt == "pdf":
        pdf_data = _generate_pdf_report(report_payload)
        filename = _get_export_filename(report_payload, "pdf")
        return Response(
            pdf_data,
            mimetype="application/pdf",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            status=200,
        )

    elif clean_fmt == "json":
        filename = _get_export_filename(report_payload, "json")
        response = jsonify(report_payload)
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response, 200
