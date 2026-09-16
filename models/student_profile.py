"""
StudentProfile model.

One-to-one extension of the User model for students. Holds academic info
and the FK to the room the student is assigned to (nullable until admin
assigns a room).
"""

from datetime import datetime, timezone
from models import db


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    student_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    course = db.Column(db.String(120), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    hostel = db.Column(db.String(80), nullable=True)
    block = db.Column(db.String(20), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # Relationships
    user = db.relationship("User", back_populates="profile")
    room = db.relationship("Room", back_populates="occupants")

    def __repr__(self):
        return f"<StudentProfile {self.student_id}>"
