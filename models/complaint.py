"""
Complaint model.

Stores student complaints and their resolution status.
"""

from datetime import datetime, timezone
from models import db


class ComplaintStatus:
    PENDING = "Pending"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"

    ALL = [
        PENDING,
        ASSIGNED,
        IN_PROGRESS,
        RESOLVED,
        REJECTED
    ]


class ComplaintCategory:
    ELECTRICAL = "Electrical"
    PLUMBING = "Plumbing"
    CLEANING = "Cleaning"
    INTERNET = "Internet"
    ROOM = "Room"
    OTHER = "Other"

    ALL = [
        ELECTRICAL,
        PLUMBING,
        CLEANING,
        INTERNET,
        ROOM,
        OTHER
    ]


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default=ComplaintStatus.PENDING
    )

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    resolution_notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    student = db.relationship(
        "User",
        foreign_keys=[student_id],
        backref=db.backref(
            "complaints",
            lazy="dynamic"
        )
    )

    assigned_staff = db.relationship(
        "User",
        foreign_keys=[assigned_staff_id],
        backref=db.backref(
            "assigned_complaints",
            lazy="dynamic"
        )
    )

    def __repr__(self):
        return f"<Complaint #{self.id} {self.title} ({self.status})>"