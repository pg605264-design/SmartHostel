"""
SmartHostel — Application Configuration

Loads settings from environment variables (.env) so no secrets are
hardcoded. Structured so swapping SQLite for PostgreSQL later only
requires changing SQLALCHEMY_DATABASE_URI.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # --- Database ---
    # Default: SQLite file under /database. To move to Postgres later,
    # just set DATABASE_URL, e.g. postgresql://user:pass@host/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'smarthostel.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Sessions / Auth ---
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set SESSION_COOKIE_SECURE = True once served over HTTPS in production.
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"

    # --- Uploads (used from Phase 5 onward, defined now for structure) ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # --- Misc ---
    DEBUG = os.environ.get("FLASK_ENV", "development") == "development"
