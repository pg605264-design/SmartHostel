"""
CleaningRequest model.

Holds student cleaning requests and staff task assignments.
"""

from datetime import datetime, timezone
from models import db


class CleaningStatus:
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

    ALL = [PENDING, SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED]


class CleaningRequest(db.Model):
    __tablename__ = "cleaning_requests"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("rooms.id"),
        nullable=True
    )

    preferred_date = db.Column(
        db.String(20),
        nullable=False
    )  # e.g. YYYY-MM-DD

    preferred_slot = db.Column(
        db.String(50),
        nullable=False
    )  # e.g. 10:00 AM - 11:00 AM

    notes = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default=CleaningStatus.PENDING
    )

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # Relationships
    student = db.relationship(
        "User",
        foreign_keys=[student_id],
        backref=db.backref(
            "cleaning_requests",
            lazy="dynamic"
        )
    )

    assigned_staff = db.relationship(
        "User",
        foreign_keys=[assigned_staff_id],
        backref=db.backref(
            "assigned_cleanings",
            lazy="dynamic"
        )
    )

    room = db.relationship(
        "Room",
        backref=db.backref(
            "cleaning_requests",
            lazy="dynamic"
        )
    )

    def __repr__(self):
        return f"<CleaningRequest #{self.id} Room {self.room_id} ({self.status})>"