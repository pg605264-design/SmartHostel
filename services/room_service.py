"""
Room service — CRUD, assignment, and capacity management.
"""

from models import db
from models.room import Room, RoomStatus
from models.student_profile import StudentProfile


def create_room(data: dict) -> tuple[Room | None, str | None]:
    hostel = (data.get("hostel") or "").strip()
    block = (data.get("block") or "").strip()
    room_number = (data.get("room_number") or "").strip()
    room_type = (data.get("room_type") or "").strip()
    floor = data.get("floor")
    capacity = data.get("capacity")

    if not all([hostel, block, room_number, room_type]):
        return None, "Hostel, block, room number, and room type are required."

    try:
        floor = int(floor)
    except (ValueError, TypeError):
        return None, "Floor must be a number."

    try:
        capacity = int(capacity)
        if capacity < 1:
            raise ValueError
    except (ValueError, TypeError):
        return None, "Capacity must be a positive number."

    existing = Room.query.filter_by(hostel=hostel, block=block, room_number=room_number).first()
    if existing:
        return None, f"Room {block}-{room_number} already exists in {hostel}."

    room = Room(
        hostel=hostel,
        block=block,
        floor=floor,
        room_number=room_number,
        room_type=room_type,
        capacity=capacity,
        status=data.get("status", RoomStatus.AVAILABLE),
    )
    db.session.add(room)
    db.session.commit()
    return room, None


def update_room(room: Room, data: dict) -> str | None:
    room.hostel = (data.get("hostel") or room.hostel).strip()
    room.block = (data.get("block") or room.block).strip()
    room.room_number = (data.get("room_number") or room.room_number).strip()
    room.room_type = (data.get("room_type") or room.room_type).strip()

    try:
        room.floor = int(data.get("floor", room.floor))
    except (ValueError, TypeError):
        return "Floor must be a number."

    try:
        cap = int(data.get("capacity", room.capacity))
        if cap < 1:
            raise ValueError
        if cap < room.occupancy_count:
            return f"Cannot reduce capacity below current occupancy ({room.occupancy_count})."
        room.capacity = cap
    except (ValueError, TypeError):
        return "Capacity must be a positive number."

    new_status = data.get("status")
    if new_status and new_status in RoomStatus.ALL:
        room.status = new_status

    db.session.commit()
    return None


def assign_student_to_room(profile: StudentProfile, room: Room) -> str | None:
    if profile.room_id:
        if profile.room_id == room.id:
            return "Student is already assigned to this room."
        return "Student is already assigned to another room. Remove them first."

    if room.status not in RoomStatus.ASSIGNABLE:
        return f"Cannot assign to a room with status '{room.status}'."

    if room.is_full:
        return "Room capacity reached."

    profile.room_id = room.id
    profile.hostel = room.hostel
    profile.block = room.block
    room.auto_update_status()
    db.session.commit()
    return None


def remove_student_from_room(profile: StudentProfile) -> str | None:
    if not profile.room_id:
        return "Student is not assigned to any room."

    room = profile.room
    profile.room_id = None
    db.session.flush()
    room.auto_update_status()
    db.session.commit()
    return None


def get_rooms(hostel=None, block=None, status=None, search=None):
    q = Room.query
    if hostel:
        q = q.filter(Room.hostel == hostel)
    if block:
        q = q.filter(Room.block == block)
    if status:
        q = q.filter(Room.status == status)
    if search:
        q = q.filter(
            db.or_(
                Room.room_number.ilike(f"%{search}%"),
                Room.hostel.ilike(f"%{search}%"),
                Room.block.ilike(f"%{search}%"),
            )
        )
    return q.order_by(Room.hostel, Room.block, Room.room_number).all()


def get_room_stats() -> dict:
    total = Room.query.count()
    occupied = Room.query.filter_by(status=RoomStatus.OCCUPIED).count()
    available = Room.query.filter_by(status=RoomStatus.AVAILABLE).count()
    maintenance = Room.query.filter(
        Room.status.in_([RoomStatus.MAINTENANCE, RoomStatus.CLEANING, RoomStatus.OUT_OF_SERVICE])
    ).count()
    return {
        "total": total,
        "occupied": occupied,
        "available": available,
        "maintenance": maintenance,
    }
