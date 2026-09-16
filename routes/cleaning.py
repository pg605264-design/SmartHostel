"""
Cleaning routes — request room cleaning, view queue, update cleaning status.
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.user import User, Role
from models.cleaning import CleaningRequest, CleaningStatus
from models.notification import Notification
from utils.decorators import role_required

cleaning_bp = Blueprint("cleaning", __name__)


@cleaning_bp.route("/cleaning")
@login_required
def index():
    status_filter = request.args.get("status", "").strip()

    if current_user.role == Role.STUDENT:
        q = CleaningRequest.query.filter_by(student_id=current_user.id)
    elif current_user.role == Role.CLEANING_STAFF:
        q = CleaningRequest.query.filter(
            db.or_(
                CleaningRequest.assigned_staff_id == current_user.id,
                CleaningRequest.status == CleaningStatus.PENDING
            )
        )
    else:
        q = CleaningRequest.query

    if status_filter and status_filter in CleaningStatus.ALL:
        q = q.filter(CleaningRequest.status == status_filter)

    requests_list = q.order_by(CleaningRequest.created_at.desc()).all()
    cleaning_staff_list = User.query.filter_by(role=Role.CLEANING_STAFF, is_active_account=True).all()

    return render_template(
        "cleaning/index.html",
        requests=requests_list,
        status_filter=status_filter,
        statuses=CleaningStatus.ALL,
        cleaning_staff=cleaning_staff_list
    )


@cleaning_bp.route("/cleaning/request", methods=["GET", "POST"])
@login_required
def request_cleaning():
    if request.method == "POST":
        preferred_date = request.form.get("preferred_date", "").strip()
        preferred_slot = request.form.get("preferred_slot", "").strip()
        notes = request.form.get("notes", "").strip()

        if not preferred_date or not preferred_slot:
            flash("Please choose a date and time slot.", "error")
            return render_template("cleaning/request.html")

        room = current_user.profile.room if current_user.profile else None

        req = CleaningRequest(
            student_id=current_user.id,
            room_id=room.id if room else None,
            preferred_date=preferred_date,
            preferred_slot=preferred_slot,
            notes=notes,
            status=CleaningStatus.PENDING
        )
        db.session.add(req)
        
        # Add Notification for student
        notif = Notification(
            user_id=current_user.id,
            title="Cleaning Request Submitted",
            message=f"Your room cleaning request for {preferred_date} ({preferred_slot}) has been logged.",
            icon="fa-broom",
            link=url_for("cleaning.index")
        )
        db.session.add(notif)
        db.session.commit()

        flash("Cleaning request submitted successfully!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("cleaning/request.html")


@cleaning_bp.route("/cleaning/<int:request_id>/update-status", methods=["POST"])
@login_required
def update_status(request_id):
    if current_user.role not in [Role.CLEANING_STAFF, Role.ADMIN]:
        flash("Unauthorized to update cleaning tasks.", "error")
        return redirect(url_for("cleaning.index"))

    req = db.get_or_404(CleaningRequest, request_id)
    new_status = request.form.get("status")
    assigned_staff_id = request.form.get("assigned_staff_id", type=int)

    if new_status and new_status in CleaningStatus.ALL:
        req.status = new_status
        if new_status == CleaningStatus.COMPLETED:
            req.completed_at = datetime.now(timezone.utc)

        # Notify student
        notif = Notification(
            user_id=req.student_id,
            title=f"Cleaning Request {new_status}",
            message=f"Your cleaning request for {req.preferred_date} is now {new_status}.",
            icon="fa-broom",
            link=url_for("cleaning.index")
        )
        db.session.add(notif)

    if assigned_staff_id:
        req.assigned_staff_id = assigned_staff_id
    elif current_user.role == Role.CLEANING_STAFF and not req.assigned_staff_id:
        req.assigned_staff_id = current_user.id

    db.session.commit()
    flash("Cleaning request status updated.", "success")
    return redirect(url_for("cleaning.index"))
