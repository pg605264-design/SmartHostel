"""
Profile routes — view profile, edit profile, and change password.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.user import Role
from utils.decorators import role_required
from services.profile_service import validate_profile_update, update_profile

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def index():
    profile = current_user.profile
    room = profile.room if profile else None
    return render_template("profile/index.html", profile=profile, room=room)


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "course": request.form.get("course"),
            "year": request.form.get("year"),
        }

        errors = validate_profile_update(current_user, data)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("profile/edit.html", form_data=data)

        update_profile(current_user, data)
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.index"))

    form_data = {
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone or "",
        "course": current_user.profile.course or "" if current_user.profile else "",
        "year": current_user.profile.year or "" if current_user.profile else "",
    }
    return render_template("profile/edit.html", form_data=form_data)


@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    current_pw = request.form.get("current_password", "")
    new_pw = request.form.get("new_password", "")
    confirm_pw = request.form.get("confirm_password", "")

    if not current_user.check_password(current_pw):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("profile.index"))

    if len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for("profile.index"))

    if new_pw != confirm_pw:
        flash("New passwords do not match.", "error")
        return redirect(url_for("profile.index"))

    current_user.set_password(new_pw)
    db.session.commit()
    flash("Password updated successfully.", "success")
    return redirect(url_for("profile.index"))
