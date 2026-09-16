"""
User model.

Holds authentication data and the user's role. Later phases attach a
StudentProfile (1:1) for students, and link Room/Timetable/Complaint/
CleaningRequest records via foreign keys back to this table's id.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from models import db


class Role:
    """Central place for the four supported roles, to avoid typo bugs."""
    STUDENT = "student"
    CLEANING_STAFF = "cleaning_staff"
    MAINTENANCE_STAFF = "maintenance_staff"
    ADMIN = "admin"

    ALL = [STUDENT, CLEANING_STAFF, MAINTENANCE_STAFF, ADMIN]


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default=Role.STUDENT)
    phone = db.Column(db.String(20), nullable=True)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # One-to-one: student user has a profile
    profile = db.relationship("StudentProfile", back_populates="user", uselist=False, lazy="joined")

    # --- Password helpers ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # --- Flask-Login required property ---
    # UserMixin already provides is_authenticated/is_anonymous/get_id.
    # We override `is_active` to respect our own is_active_account flag,
    # so admins can disable an account and it is instantly logged out.
    @property
    def is_active(self):
        return self.is_active_account

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
