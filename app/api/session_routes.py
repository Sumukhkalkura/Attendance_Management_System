"""FR-15 user logout.

Kept separate from ``auth_routes`` because ``/api/logout`` is registered
after the enrollment routes in the original URL order.
"""

from flask import jsonify, session

from ..auth import login_required
from .blueprint import api

# =====================================================================
# FR-15: User Logout
# =====================================================================

@api.post("/logout")
@login_required()
def logout():
    """
    Log out the currently authenticated user.

    Clears the Flask session so the user can no longer access
    protected endpoints without logging in again.
    """

    session.clear()

    return jsonify(
        message="Logged out successfully"
    ), 200
