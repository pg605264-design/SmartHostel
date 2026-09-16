"""
Dashboard routes.

Renders role-aware dashboards with REAL database statistics, upcoming timetable,
cleaning progress, complaint feeds, notification center, and activity timelines.
"""

from datetime import datetime, time
from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash
from flask_login import login_required, current_user

from models import db
from models.user import User, Role
from models.room import Room, RoomStatus
from models.student_profile import StudentProfile
from models.cleaning import CleaningRequest, CleaningStatus
from models.complaint import Complaint, ComplaintStatus, ComplaintCategory
from models.timetable import Timetable
from models.notification import Notification


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():

    # ==========================================================
    # BASIC DATE / GREETING INFORMATION
    # ==========================================================

    now = datetime.now()
    hour = now.hour

    if hour < 12:
        greeting = "Good Morning"
    elif hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"


    # ==========================================================
    # USER NOTIFICATIONS
    # ==========================================================

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).limit(10).all()

    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()


    # ==========================================================
    # COMMON CONTEXT
    # ==========================================================

    ctx = {
        "greeting": greeting,
        "today": now.strftime("%A, %d %B %Y"),
        "today_day_name": now.strftime("%A"),
        "notifications": notifications,
        "unread_notifications_count": unread_count,
        "categories": ComplaintCategory.ALL,
    }


    # ==========================================================
    # STUDENT DASHBOARD
    # ==========================================================

    if current_user.role == Role.STUDENT:

        profile = current_user.profile

        room = profile.room if profile else None

        roommates = (
            [
                p for p in room.occupants.all()
                if p.user_id != current_user.id
            ]
            if room
            else []
        )


        # ------------------------------------------------------
        # Next Cleaning Request
        # ------------------------------------------------------

        next_cleaning_req = CleaningRequest.query.filter(
            CleaningRequest.student_id == current_user.id,
            CleaningRequest.status.in_([
                CleaningStatus.PENDING,
                CleaningStatus.SCHEDULED,
                CleaningStatus.IN_PROGRESS
            ])
        ).order_by(
            CleaningRequest.created_at.desc()
        ).first()


        next_cleaning_date = (
            f"{next_cleaning_req.preferred_date} "
            f"({next_cleaning_req.preferred_slot})"
            if next_cleaning_req
            else "Not scheduled"
        )


        # ------------------------------------------------------
        # Complaint Statistics
        # ------------------------------------------------------

        pending_complaints_count = Complaint.query.filter(
            Complaint.student_id == current_user.id,
            Complaint.status.in_([
                ComplaintStatus.PENDING,
                ComplaintStatus.ASSIGNED,
                ComplaintStatus.IN_PROGRESS
            ])
        ).count()


        resolved_complaints_count = Complaint.query.filter_by(
            student_id=current_user.id,
            status=ComplaintStatus.RESOLVED
        ).count()


        # ------------------------------------------------------
        # Room Status
        # ------------------------------------------------------

        room_status_text = (
            f"Room {room.display_name}"
            if room
            else "Not linked yet"
        )


        # ------------------------------------------------------
        # Dynamic Quick Status Banner
        # ------------------------------------------------------

        if pending_complaints_count > 0:

            quick_status_msg = (
                f"You have {pending_complaints_count} "
                f"active complaint(s) in progress."
            )

            quick_status_type = "warning"

        elif next_cleaning_req:

            quick_status_msg = (
                f"Your next room cleaning is scheduled "
                f"for {next_cleaning_req.preferred_date}."
            )

            quick_status_type = "info"

        else:

            quick_status_msg = (
                "Everything looks good! Your room services "
                "and schedule are up to date."
            )

            quick_status_type = "success"


        # ------------------------------------------------------
        # Today's Timetable / Classes
        # ------------------------------------------------------

        today_day = now.strftime("%A")

        course = profile.course if profile else None
        year = profile.year if profile else None


        today_classes = Timetable.query.filter(
            Timetable.day == today_day,
            db.or_(
                Timetable.user_id == current_user.id,

                db.and_(
                    Timetable.course == course,
                    Timetable.year == year
                ),

                db.and_(
                    Timetable.course.is_(None),
                    Timetable.user_id.is_(None)
                )
            )
        ).order_by(
            Timetable.start_time
        ).all()


        next_class = (
            today_classes[0]
            if today_classes
            else None
        )


        # ------------------------------------------------------
        # Latest Cleaning Progress
        # ------------------------------------------------------

        latest_cleaning = CleaningRequest.query.filter_by(
            student_id=current_user.id
        ).order_by(
            CleaningRequest.created_at.desc()
        ).first()


        cleaning_step = 0

        if latest_cleaning:

            if latest_cleaning.status == CleaningStatus.PENDING:
                cleaning_step = 1

            elif latest_cleaning.status == CleaningStatus.SCHEDULED:
                cleaning_step = 2

            elif latest_cleaning.status == CleaningStatus.IN_PROGRESS:
                cleaning_step = 3

            elif latest_cleaning.status == CleaningStatus.COMPLETED:
                cleaning_step = 4


        # ------------------------------------------------------
        # Recent Complaints
        # ------------------------------------------------------

        recent_complaints = Complaint.query.filter_by(
            student_id=current_user.id
        ).order_by(
            Complaint.created_at.desc()
        ).limit(4).all()


        # ------------------------------------------------------
        # Activity Timeline
        # ------------------------------------------------------

        timeline = []


        for c in recent_complaints:

            timeline.append({
                "title": f"Complaint '{c.title}'",
                "desc": f"Status is {c.status}",
                "date": c.updated_at or c.created_at,
                "icon": "fa-wrench",
                "type": "complaint"
            })


        all_cleanings = CleaningRequest.query.filter_by(
            student_id=current_user.id
        ).order_by(
            CleaningRequest.created_at.desc()
        ).limit(3).all()


        for cl in all_cleanings:

            timeline.append({
                "title": f"Cleaning Request ({cl.preferred_date})",
                "desc": f"Status: {cl.status}",
                "date": cl.completed_at or cl.created_at,
                "icon": "fa-broom",
                "type": "cleaning"
            })


        timeline.sort(
            key=lambda x: x["date"],
            reverse=True
        )


        # ------------------------------------------------------
        # Student Context
        # ------------------------------------------------------

        ctx.update({
            "profile": profile,
            "room": room,
            "roommates": roommates,
            "next_cleaning_date": next_cleaning_date,
            "pending_complaints_count": pending_complaints_count,
            "resolved_complaints_count": resolved_complaints_count,
            "room_status_text": room_status_text,
            "quick_status_msg": quick_status_msg,
            "quick_status_type": quick_status_type,
            "today_classes": today_classes,
            "next_class": next_class,
            "latest_cleaning": latest_cleaning,
            "cleaning_step": cleaning_step,
            "recent_complaints": recent_complaints,
            "timeline": timeline[:5],
        })


    # ==========================================================
    # CLEANING STAFF DASHBOARD
    # ==========================================================

    elif current_user.role == Role.CLEANING_STAFF:

        assigned_tasks = CleaningRequest.query.filter(
            db.or_(
                CleaningRequest.assigned_staff_id == current_user.id,
                CleaningRequest.status == CleaningStatus.PENDING
            )
        ).order_by(
            CleaningRequest.created_at.desc()
        ).all()


        pending_count = sum(
            1
            for r in assigned_tasks
            if r.status in [
                CleaningStatus.PENDING,
                CleaningStatus.SCHEDULED
            ]
        )


        completed_count = CleaningRequest.query.filter_by(
            assigned_staff_id=current_user.id,
            status=CleaningStatus.COMPLETED
        ).count()


        ctx.update({
            "assigned_count": len(assigned_tasks),
            "pending_count": pending_count,
            "completed_count": completed_count,
            "assigned_tasks": assigned_tasks[:5],
        })


    # ==========================================================
    # MAINTENANCE STAFF DASHBOARD
    # ==========================================================

    elif current_user.role == Role.MAINTENANCE_STAFF:

        assigned_complaints = Complaint.query.filter(
            db.or_(
                Complaint.assigned_staff_id == current_user.id,
                Complaint.status == ComplaintStatus.PENDING
            )
        ).order_by(
            Complaint.created_at.desc()
        ).all()


        # ------------------------------------------------------
        # Dashboard Statistics
        # ------------------------------------------------------

        assigned_count = len(assigned_complaints)


        # Electrical and Plumbing are treated as
        # priority/emergency complaints.
        emergency_count = sum(
            1
            for c in assigned_complaints
            if c.category in ["Electrical", "Plumbing"]
        )


        pending_count = sum(
            1
            for c in assigned_complaints
            if c.status == ComplaintStatus.PENDING
        )


        in_progress_count = sum(
            1
            for c in assigned_complaints
            if c.status == ComplaintStatus.IN_PROGRESS
        )


        resolved_count = Complaint.query.filter_by(
            assigned_staff_id=current_user.id,
            status=ComplaintStatus.RESOLVED
        ).count()


        # ------------------------------------------------------
        # Priority Complaints
        # ------------------------------------------------------

        emergency_complaints = [
            c
            for c in assigned_complaints
            if c.category in ["Electrical", "Plumbing"]
            and c.status != ComplaintStatus.RESOLVED
        ]


        # ------------------------------------------------------
        # Maintenance Context
        # ------------------------------------------------------

        ctx.update({
            "assigned_count": assigned_count,
            "emergency_count": emergency_count,
            "pending_count": pending_count,
            "in_progress_count": in_progress_count,
            "resolved_count": resolved_count,
            "assigned_complaints": assigned_complaints[:5],
            "emergency_complaints": emergency_complaints[:3],
        })


    # ==========================================================
    # ADMIN DASHBOARD
    # ==========================================================

    else:

        total_students = User.query.filter_by(
            role=Role.STUDENT,
            is_active_account=True
        ).count()


        total_rooms = Room.query.count()


        occupied_rooms = Room.query.filter_by(
            status=RoomStatus.OCCUPIED
        ).count()


        available_rooms = Room.query.filter_by(
            status=RoomStatus.AVAILABLE
        ).count()


        pending_complaints_count = Complaint.query.filter(
            Complaint.status.in_([
                ComplaintStatus.PENDING,
                ComplaintStatus.ASSIGNED,
                ComplaintStatus.IN_PROGRESS
            ])
        ).count()


        active_cleanings = CleaningRequest.query.filter(
            CleaningRequest.status.in_([
                CleaningStatus.PENDING,
                CleaningStatus.SCHEDULED,
                CleaningStatus.IN_PROGRESS
            ])
        ).count()


        recent_complaints = Complaint.query.order_by(
            Complaint.created_at.desc()
        ).limit(5).all()


        ctx.update({
            "total_students": total_students,
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "available_rooms": available_rooms,
            "pending_complaints_count": pending_complaints_count,
            "active_cleanings": active_cleanings,
            "recent_complaints": recent_complaints,
        })


    # ==========================================================
    # RENDER DASHBOARD
    # ==========================================================

    return render_template(
        "dashboard/index.html",
        **ctx
    )


# ==============================================================
# MARK SINGLE NOTIFICATION AS READ
# ==============================================================

@dashboard_bp.route(
    "/notifications/mark-read/<int:notification_id>",
    methods=["POST"]
)
@login_required
def mark_notification_read(notification_id):

    notif = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()


    notif.is_read = True

    db.session.commit()


    return jsonify({
        "success": True
    })


# ==============================================================
# MARK ALL NOTIFICATIONS AS READ
# ==============================================================

@dashboard_bp.route(
    "/notifications/mark-all-read",
    methods=["POST"]
)
@login_required
def mark_all_notifications_read():

    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({
        "is_read": True
    })


    db.session.commit()


    flash(
        "All notifications marked as read.",
        "success"
    )


    return redirect(
        request.referrer or url_for("dashboard.index")
    )