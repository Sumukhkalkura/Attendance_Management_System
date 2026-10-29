"""Frontend page routes: the login screen and role-based dashboards.

Pages only render the HTML shell; all data is loaded from the /api routes,
which enforce their own authentication and authorization.
"""

import sqlite3

from flask import Blueprint, redirect, render_template, session, url_for

from .db import get_db

pages = Blueprint("pages", __name__)

ROLE_PAGES = {
    "admin": "pages.admin_dashboard",
    "teacher": "pages.teacher_dashboard",
    "student": "pages.student_dashboard",
}


def current_page_user():
    """Return the active logged-in user for page rendering, or None."""
    user_id = session.get("user_id")

    if user_id is None:
        return None

    try:
        user = get_db().execute(
            "SELECT id, username, role, active FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
    except sqlite3.Error:
        return None

    if user is None or not user["active"]:
        session.clear()
        return None

    return user


def render_dashboard(role, template):
    """Render a dashboard for its role; redirect everyone else."""
    user = current_page_user()

    if user is None:
        return redirect(url_for("pages.login_page"))

    if user["role"] != role:
        return redirect(url_for(ROLE_PAGES[user["role"]]))

    return render_template(template, user=user)


@pages.get("/login")
def login_page():
    user = current_page_user()

    if user is not None:
        return redirect(url_for(ROLE_PAGES[user["role"]]))

    return render_template("login.html")


@pages.get("/dashboard")
def dashboard():
    """Send a logged-in user to the dashboard for their role."""
    user = current_page_user()

    if user is None:
        return redirect(url_for("pages.login_page"))

    return redirect(url_for(ROLE_PAGES[user["role"]]))


@pages.get("/admin")
def admin_dashboard():
    return render_dashboard("admin", "admin.html")


@pages.get("/teacher")
def teacher_dashboard():
    return render_dashboard("teacher", "teacher.html")


@pages.get("/student")
def student_dashboard():
    return render_dashboard("student", "student.html")
