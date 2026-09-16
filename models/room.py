"""
Room model.

Represents a physical hostel room. Each room belongs to a hostel/block/floor
and can hold up to `capacity` students via the StudentProfile.room_id FK.
"""

from datetime import datetime, timezone
from models import db


class RoomStatus:
    """Allowed room statuses."""
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"
    CLEANING = "Cleaning"
    OUT_OF_SERVICE = "Out of Service"

    ALL = [AVAILABLE, OCCUPIED, MAINTENANCE, CLEANING, OUT_OF_SERVICE]
    ASSIGNABLE = [AVAILABLE, OCCUPIED]


class RoomType:
    """Common room types."""
    SINGLE = "Single"
    DOUBLE = "Double"
    TRIPLE = "Triple"
    QUAD = "Quad"

    ALL = [SINGLE, DOUBLE, TRIPLE, QUAD]


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    hostel = db.Column(db.String(80), nullable=False, index=True)
    block = db.Column(db.String(20), nullable=False, index=True)
    floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    room_type = db.Column(db.String(30), nullable=False, default=RoomType.DOUBLE)
    capacity = db.Column(db.Integer, nullable=False, default=2)
    status = db.Column(db.String(30), nullable=False, default=RoomStatus.AVAILABLE)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # One-to-many: a room has many occupants (StudentProfile rows)
    occupants = db.relationship("StudentProfile", back_populates="room", lazy="dynamic")

    __table_args__ = (
        db.UniqueConstraint("hostel", "block", "room_number", name="uq_room_identity"),
    )

    @property
    def occupancy_count(self):
        return self.occupants.count()

    @property
    def is_full(self):
        return self.occupancy_count >= self.capacity

    @property
    def display_name(self):
        return f"{self.block}-{self.room_number}"

    @property
    def can_accept_student(self):
        return self.status in RoomStatus.ASSIGNABLE and not self.is_full

    def auto_update_status(self):
        """Set Available/Occupied based on current occupancy.
        Does NOT override admin-set statuses like Maintenance."""
        if self.status in (RoomStatus.MAINTENANCE, RoomStatus.CLEANING, RoomStatus.OUT_OF_SERVICE):
            return
        self.status = RoomStatus.OCCUPIED if self.occupancy_count > 0 else RoomStatus.AVAILABLE

    def __repr__(self):
        return f"<Room {self.display_name} ({self.hostel})>"
