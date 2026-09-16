"""
Complaints routes — raise complaints, view complaint details, assign & update resolution status.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.user import User, Role
from models.complaint import Complaint, ComplaintStatus, ComplaintCategory
from models.notification import Notification
from utils.decorators import role_required

complaint_bp = Blueprint("complaint", __name__)


@complaint_bp.route("/complaints")
@login_required
def index():
    status_filter = request.args.get("status", "").strip()
    category_filter = request.args.get("category", "").strip()

    if current_user.role == Role.STUDENT:
        q = Complaint.query.filter_by(student_id=current_user.id)
    elif current_user.role == Role.MAINTENANCE_STAFF:
        q = Complaint.query.filter(
            db.or_(
                Complaint.assigned_staff_id == current_user.id,
                Complaint.status == ComplaintStatus.PENDING
            )
        )
    else:
        q = Complaint.query

    if status_filter and status_filter in ComplaintStatus.ALL:
        q = q.filter(Complaint.status == status_filter)
    if category_filter and category_filter in ComplaintCategory.ALL:
        q = q.filter(Complaint.category == category_filter)

    complaints_list = q.order_by(Complaint.created_at.desc()).all()
    maintenance_staff = User.query.filter_by(role=Role.MAINTENANCE_STAFF, is_active_account=True).all()

    return render_template(
        "complaints/index.html",
        complaints=complaints_list,
        status_filter=status_filter,
        category_filter=category_filter,
        statuses=ComplaintStatus.ALL,
        categories=ComplaintCategory.ALL,
        staff_members=maintenance_staff
    )


@complaint_bp.route("/complaints/raise", methods=["GET", "POST"])
@login_required
def raise_complaint():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not category or not title or not description:
            flash("Category, title, and description are required.", "error")
            return render_template("complaints/raise.html", categories=ComplaintCategory.ALL)

        complaint = Complaint(
            student_id=current_user.id,
            category=category,
            title=title,
            description=description,
            status=ComplaintStatus.PENDING
        )
        db.session.add(complaint)
        db.session.flush()

        # Add Notification for student
        notif = Notification(
            user_id=current_user.id,
            title=f"Complaint #{complaint.id} Filed",
            message=f"Your complaint '{title}' has been received and logged.",
            icon="fa-wrench",
            link=url_for("complaint.detail", complaint_id=complaint.id)
        )
        db.session.add(notif)
        db.session.commit()

        flash(f"Complaint '{title}' submitted successfully!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("complaints/raise.html", categories=ComplaintCategory.ALL)


@complaint_bp.route("/complaints/<int:complaint_id>")
@login_required
def detail(complaint_id):
    complaint = db.get_or_404(Complaint, complaint_id)

    if current_user.role == Role.STUDENT and complaint.student_id != current_user.id:
        flash("Unauthorized access to this complaint.", "error")
        return redirect(url_for("complaint.index"))

    staff_members = User.query.filter(
        User.role.in_([Role.MAINTENANCE_STAFF, Role.CLEANING_STAFF]),
        User.is_active_account == True
    ).all()

    return render_template(
        "complaints/detail.html",
        complaint=complaint,
        statuses=ComplaintStatus.ALL,
        staff_members=staff_members
    )


@complaint_bp.route("/complaints/<int:complaint_id>/update-status", methods=["POST"])
@login_required
def update_status(complaint_id):
    if current_user.role not in [Role.ADMIN, Role.MAINTENANCE_STAFF, Role.CLEANING_STAFF]:
        flash("Unauthorized to update complaint status.", "error")
        return redirect(url_for("complaint.index"))

    complaint = db.get_or_404(Complaint, complaint_id)
    new_status = request.form.get("status")
    assigned_staff_id = request.form.get("assigned_staff_id", type=int)
    resolution_notes = request.form.get("resolution_notes", "").strip()

    if new_status and new_status in ComplaintStatus.ALL:
        complaint.status = new_status

    if assigned_staff_id is not None:
        complaint.assigned_staff_id = assigned_staff_id if assigned_staff_id > 0 else None
    elif current_user.role in [Role.MAINTENANCE_STAFF, Role.CLEANING_STAFF] and not complaint.assigned_staff_id:
        complaint.assigned_staff_id = current_user.id

    if resolution_notes:
        complaint.resolution_notes = resolution_notes

    # Create notification for student
    notif = Notification(
        user_id=complaint.student_id,
        title=f"Complaint #{complaint.id} {complaint.status}",
        message=f"Complaint '{complaint.title}' status was updated to {complaint.status}.",
        icon="fa-wrench",
        link=url_for("complaint.detail", complaint_id=complaint.id)
    )
    db.session.add(notif)
    db.session.commit()

    flash(f"Complaint #{complaint.id} status updated to '{complaint.status}'.", "success")
    return redirect(url_for("complaint.detail", complaint_id=complaint.id))
