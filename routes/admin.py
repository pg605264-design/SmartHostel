"""
Admin routes — full management dashboard for rooms, students, and staff.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db
from models.user import User, Role
from models.student_profile import StudentProfile
from models.room import Room, RoomStatus, RoomType
from utils.decorators import role_required
from services.room_service import (
    create_room, update_room, assign_student_to_room,
    remove_student_from_room, get_rooms, get_room_stats,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@role_required(Role.ADMIN)
def dashboard():
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning"
    elif hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    total_students = User.query.filter_by(role=Role.STUDENT, is_active_account=True).count()
    room_stats = get_room_stats()
    pending_assignments = StudentProfile.query.filter_by(room_id=None).count()
    active_staff = User.query.filter(
        User.role.in_([Role.CLEANING_STAFF, Role.MAINTENANCE_STAFF]),
        User.is_active_account == True,
    ).count()

    return render_template(
        "admin/dashboard.html",
        greeting=greeting,
        today=datetime.now().strftime("%A, %d %B %Y"),
        total_students=total_students,
        room_stats=room_stats,
        pending_assignments=pending_assignments,
        active_staff=active_staff,
    )


@admin_bp.route("/students")
@login_required
@role_required(Role.ADMIN)
def students():
    search = request.args.get("search", "").strip()
    hostel_filter = request.args.get("hostel", "").strip()
    block_filter = request.args.get("block", "").strip()
    status_filter = request.args.get("status", "").strip()

    q = User.query.filter_by(role=Role.STUDENT)

    if status_filter == "active":
        q = q.filter_by(is_active_account=True)
    elif status_filter == "inactive":
        q = q.filter_by(is_active_account=False)

    if search:
        q = q.filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    students_list = q.order_by(User.name).all()

    if hostel_filter or block_filter:
        filtered = []
        for s in students_list:
            if s.profile:
                if hostel_filter and s.profile.hostel != hostel_filter:
                    continue
                if block_filter and s.profile.block != block_filter:
                    continue
            else:
                continue
            filtered.append(s)
        students_list = filtered

    hostels = db.session.query(Room.hostel).distinct().order_by(Room.hostel).all()
    blocks = db.session.query(Room.block).distinct().order_by(Room.block).all()

    return render_template(
        "admin/students.html",
        students=students_list,
        search=search,
        hostel_filter=hostel_filter,
        block_filter=block_filter,
        status_filter=status_filter,
        hostels=[h[0] for h in hostels],
        blocks=[b[0] for b in blocks],
    )


@admin_bp.route("/students/<int:student_id>")
@login_required
@role_required(Role.ADMIN)
def student_detail(student_id):
    user = db.get_or_404(User, student_id)
    if user.role != Role.STUDENT:
        flash("User is not a student.", "error")
        return redirect(url_for("admin.students"))

    available_rooms = Room.query.filter(
        Room.status.in_(RoomStatus.ASSIGNABLE),
    ).order_by(Room.hostel, Room.block, Room.room_number).all()
    available_rooms = [r for r in available_rooms if not r.is_full]

    return render_template(
        "admin/student_detail.html",
        student=user,
        available_rooms=available_rooms,
    )


@admin_bp.route("/students/<int:student_id>/toggle-active", methods=["POST"])
@login_required
@role_required(Role.ADMIN)
def toggle_student_active(student_id):
    user = db.get_or_404(User, student_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "error")
        return redirect(url_for("admin.student_detail", student_id=student_id))

    user.is_active_account = not user.is_active_account
    action = "activated" if user.is_active_account else "deactivated"
    db.session.commit()
    flash(f"Account {user.name} {action}.", "success")
    return redirect(url_for("admin.student_detail", student_id=student_id))


@admin_bp.route("/students/<int:student_id>/assign-room", methods=["POST"])
@login_required
@role_required(Role.ADMIN)
def assign_room_to_student(student_id):
    user = db.get_or_404(User, student_id)
    if not user.profile:
        flash("Student does not have a profile.", "error")
        return redirect(url_for("admin.student_detail", student_id=student_id))

    room_id = request.form.get("room_id", type=int)
    if not room_id:
        flash("Please select a room.", "error")
        return redirect(url_for("admin.student_detail", student_id=student_id))

    room = db.get_or_404(Room, room_id)
    error = assign_student_to_room(user.profile, room)
    if error:
        flash(error, "error")
    else:
        flash(f"Student assigned to room {room.display_name}.", "success")

    return redirect(url_for("admin.student_detail", student_id=student_id))


@admin_bp.route("/students/<int:student_id>/remove-room", methods=["POST"])
@login_required
@role_required(Role.ADMIN)
def remove_room_from_student(student_id):
    user = User.query.get_or_404(student_id)
    if not user.profile:
        flash("Student does not have a profile.", "error")
        return redirect(url_for("admin.student_detail", student_id=student_id))

    error = remove_student_from_room(user.profile)
    if error:
        flash(error, "error")
    else:
        flash("Room assignment removed.", "success")

    return redirect(url_for("admin.student_detail", student_id=student_id))


@admin_bp.route("/rooms")
@login_required
@role_required(Role.ADMIN)
def rooms():
    search = request.args.get("search", "").strip()
    hostel_filter = request.args.get("hostel", "").strip()
    block_filter = request.args.get("block", "").strip()
    status_filter = request.args.get("status", "").strip()

    rooms_list = get_rooms(
        hostel=hostel_filter or None,
        block=block_filter or None,
        status=status_filter or None,
        search=search or None,
    )

    hostels = db.session.query(Room.hostel).distinct().order_by(Room.hostel).all()
    blocks = db.session.query(Room.block).distinct().order_by(Room.block).all()

    return render_template(
        "admin/rooms.html",
        rooms=rooms_list,
        search=search,
        hostel_filter=hostel_filter,
        block_filter=block_filter,
        status_filter=status_filter,
        hostels=[h[0] for h in hostels],
        blocks=[b[0] for b in blocks],
        statuses=RoomStatus.ALL,
    )


@admin_bp.route("/rooms/create", methods=["GET", "POST"])
@login_required
@role_required(Role.ADMIN)
def create_room_view():
    if request.method == "POST":
        data = {
            "hostel": request.form.get("hostel"),
            "block": request.form.get("block"),
            "floor": request.form.get("floor"),
            "room_number": request.form.get("room_number"),
            "room_type": request.form.get("room_type"),
            "capacity": request.form.get("capacity"),
            "status": request.form.get("status", RoomStatus.AVAILABLE),
        }

        room, error = create_room(data)
        if error:
            flash(error, "error")
            return render_template("admin/room_form.html", form_data=data, is_edit=False, room_types=RoomType.ALL, statuses=RoomStatus.ALL)

        flash(f"Room {room.display_name} created.", "success")
        return redirect(url_for("admin.rooms"))

    return render_template(
        "admin/room_form.html",
        form_data={},
        is_edit=False,
        room_types=RoomType.ALL,
        statuses=RoomStatus.ALL,
    )


@admin_bp.route("/rooms/<int:room_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(Role.ADMIN)
def edit_room(room_id):
    room = db.get_or_404(Room, room_id)

    if request.method == "POST":
        data = {
            "hostel": request.form.get("hostel"),
            "block": request.form.get("block"),
            "floor": request.form.get("floor"),
            "room_number": request.form.get("room_number"),
            "room_type": request.form.get("room_type"),
            "capacity": request.form.get("capacity"),
            "status": request.form.get("status"),
        }

        error = update_room(room, data)
        if error:
            flash(error, "error")
            return render_template(
                "admin/room_form.html", form_data=data, is_edit=True, room=room,
                room_types=RoomType.ALL, statuses=RoomStatus.ALL,
            )

        flash(f"Room {room.display_name} updated.", "success")
        return redirect(url_for("admin.room_detail", room_id=room.id))

    form_data = {
        "hostel": room.hostel,
        "block": room.block,
        "floor": room.floor,
        "room_number": room.room_number,
        "room_type": room.room_type,
        "capacity": room.capacity,
        "status": room.status,
    }
    return render_template(
        "admin/room_form.html",
        form_data=form_data,
        is_edit=True,
        room=room,
        room_types=RoomType.ALL,
        statuses=RoomStatus.ALL,
    )


@admin_bp.route("/rooms/<int:room_id>")
@login_required
@role_required(Role.ADMIN)
def room_detail(room_id):
    room = db.get_or_404(Room, room_id)
    occupants = room.occupants.all()

    unassigned = StudentProfile.query.filter_by(room_id=None).join(User).filter(
        User.is_active_account == True
    ).order_by(User.name).all()

    return render_template(
        "admin/room_detail.html",
        room=room,
        occupants=occupants,
        unassigned=unassigned,
    )


@admin_bp.route("/rooms/<int:room_id>/assign", methods=["POST"])
@login_required
@role_required(Role.ADMIN)
def assign_student(room_id):
    room = db.get_or_404(Room, room_id)
    profile_id = request.form.get("profile_id", type=int)
    if not profile_id:
        flash("Please select a student.", "error")
        return redirect(url_for("admin.room_detail", room_id=room_id))

    profile = db.get_or_404(StudentProfile, profile_id)
    error = assign_student_to_room(profile, room)
    if error:
        flash(error, "error")
    else:
        flash(f"{profile.user.name} assigned to room {room.display_name}.", "success")

    return redirect(url_for("admin.room_detail", room_id=room_id))


@admin_bp.route("/rooms/<int:room_id>/remove-student", methods=["POST"])
@login_required
@role_required(Role.ADMIN)
def remove_student(room_id):
    profile_id = request.form.get("profile_id", type=int)
    if not profile_id:
        flash("No student specified.", "error")
        return redirect(url_for("admin.room_detail", room_id=room_id))

    profile = db.get_or_404(StudentProfile, profile_id)
    error = remove_student_from_room(profile)
    if error:
        flash(error, "error")
    else:
        flash(f"{profile.user.name} removed from room.", "success")

    return redirect(url_for("admin.room_detail", room_id=room_id))
