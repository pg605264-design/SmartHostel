"""
Central SQLAlchemy instance.

Kept in its own module (rather than inside app.py) so every model file
and every route file can `from models import db` without circular
imports.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models here so Flask-Migrate / db.create_all() can discover them
from models.user import User  # noqa: E402,F401
from models.room import Room  # noqa: E402,F401
from models.student_profile import StudentProfile  # noqa: E402,F401
from models.timetable import Timetable  # noqa: E402,F401
from models.cleaning import CleaningRequest, CleaningStatus  # noqa: E402,F401
from models.complaint import Complaint, ComplaintStatus, ComplaintCategory  # noqa: E402,F401
from models.notification import Notification  # noqa: E402,F401
