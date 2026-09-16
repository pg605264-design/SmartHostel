"""
Authentication service — registration validation and user creation.
"""

import re
from models import db
from models.user import User, Role
from models.student_profile import StudentProfile


def validate_registration(data: dict) -> list[str]:
    errors = []

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    confirm = data.get("confirm_password") or ""
    student_id = (data.get("student_id") or "").strip()

    if not name:
        errors.append("Full name is required.")
    if not email:
        errors.append("Email is required.")
    elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("Please enter a valid email address.")
    if not student_id:
        errors.append("Student ID is required.")
    if not password:
        errors.append("Password is required.")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")

    if email and not any("email" in e.lower() for e in errors):
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
    if student_id and not any("student id" in e.lower() for e in errors):
        if StudentProfile.query.filter_by(student_id=student_id).first():
            errors.append("This Student ID is already registered.")

    return errors


def register_student(data: dict) -> User:
    user = User(
        name=data["name"].strip(),
        email=data["email"].strip().lower(),
        role=Role.STUDENT,
        phone=(data.get("phone") or "").strip() or None,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()

    profile = StudentProfile(
        user_id=user.id,
        student_id=data["student_id"].strip(),
        course=(data.get("course") or "").strip() or None,
        year=int(data["year"]) if data.get("year") else None,
    )
    db.session.add(profile)
    return user
