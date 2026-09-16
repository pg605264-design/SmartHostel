"""
Timetable model.

Holds schedule information (day, subject, start/end time, room, faculty).
Can be user-specific or global/course-based.
"""

from datetime import datetime, timezone
from models import db


class Timetable(db.Model):
    __tablename__ = "timetables"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    course = db.Column(
        db.String(120),
        nullable=True
    )

    year = db.Column(
        db.Integer,
        nullable=True
    )

    day = db.Column(
        db.String(20),
        nullable=False
    )

    subject = db.Column(
        db.String(120),
        nullable=False
    )

    start_time = db.Column(
        db.String(20),
        nullable=False
    )

    end_time = db.Column(
        db.String(20),
        nullable=False
    )

    room_number = db.Column(
        db.String(50),
        nullable=False
    )

    faculty = db.Column(
        db.String(120),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "timetable_entries",
            lazy="dynamic"
        )
    )

    def __repr__(self):
        return f"<Timetable {self.day} {self.subject} ({self.start_time}-{self.end_time})>"