"""
Profile service — student profile updates with validation.
"""

import re
from models import db
from models.user import User


def validate_profile_update(user: User, data: dict) -> list[str]:
    errors = []

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    year = data.get("year")

    if not name:
        errors.append("Name is required.")
    if not email:
        errors.append("Email is required.")
    elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("Please enter a valid email address.")

    if email:
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            errors.append("An account with this email already exists.")

    if phone and not re.match(r"^\+?[\d\s\-]{7,20}$", phone):
        errors.append("Please enter a valid phone number.")

    if year:
        try:
            y = int(year)
            if y < 1 or y > 6:
                errors.append("Year must be between 1 and 6.")
        except (ValueError, TypeError):
            errors.append("Year must be a number.")

    return errors


def update_profile(user: User, data: dict) -> None:
    user.name = data["name"].strip()
    user.email = data["email"].strip().lower()
    user.phone = (data.get("phone") or "").strip() or None

    if user.profile:
        user.profile.course = (data.get("course") or "").strip() or None
        year_val = data.get("year")
        user.profile.year = int(year_val) if year_val else None

    db.session.commit()
