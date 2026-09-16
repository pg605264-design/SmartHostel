"""
Timetable routes — view class schedule and admin/staff management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.user import Role
from models.timetable import Timetable

timetable_bp = Blueprint("timetable", __name__)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


@timetable_bp.route("/timetable")
@login_required
def index():
    if current_user.role == Role.STUDENT:
        course = current_user.profile.course if current_user.profile else None
        year = current_user.profile.year if current_user.profile else None

        entries = Timetable.query.filter(
            db.or_(
                Timetable.user_id == current_user.id,
                db.and_(Timetable.course == course, Timetable.year == year),
                db.and_(Timetable.course.is_(None), Timetable.user_id.is_(None))
            )
        ).all()
    else:
        entries = Timetable.query.all()

    schedule = {day: [] for day in DAYS}

    for entry in entries:
        if entry.day in schedule:
            schedule[entry.day].append(entry)

    for day in schedule:
        schedule[day].sort(key=lambda x: x.start_time)

    return render_template(
        "timetable/index.html",
        schedule=schedule,
        days=DAYS,
        total_entries=len(entries)
    )


@timetable_bp.route("/timetable/add", methods=["POST"])
@login_required
def add_entry():
    if current_user.role not in [
        Role.ADMIN,
        Role.MAINTENANCE_STAFF,
        Role.CLEANING_STAFF
    ]:
        flash("Unauthorized to modify timetable.", "error")
        return redirect(url_for("timetable.index"))

    day = request.form.get("day")
    subject = request.form.get("subject", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time = request.form.get("end_time", "").strip()
    room_number = request.form.get("room_number", "").strip()
    faculty = request.form.get("faculty", "").strip()
    course = request.form.get("course", "").strip() or None
    year = request.form.get("year", type=int)

    if not all([day, subject, start_time, end_time, room_number]):
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("timetable.index"))

    entry = Timetable(
        day=day,
        subject=subject,
        start_time=start_time,
        end_time=end_time,
        room_number=room_number,
        faculty=faculty,
        course=course,
        year=year
    )

    db.session.add(entry)
    db.session.commit()

    flash(f"Timetable entry for {subject} added successfully.", "success")
    return redirect(url_for("timetable.index"))


@timetable_bp.route("/timetable/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    if current_user.role != Role.ADMIN:
        flash("Only admins can delete timetable entries.", "error")
        return redirect(url_for("timetable.index"))

    entry = db.get_or_404(Timetable, entry_id)

    db.session.delete(entry)
    db.session.commit()

    flash("Timetable entry deleted.", "success")
    return redirect(url_for("timetable.index"))