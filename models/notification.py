"""
Notification model.

Stores real user notifications (cleaning updates, complaint status changes, room assignments).
"""

from datetime import datetime, timezone
from models import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default="fa-bell")
    link = db.Column(db.String(150), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic", cascade="all, delete-orphan"))

    def time_ago(self):
        now = datetime.now(timezone.utc)
        created_at = self.created_at

        # SQLite may return a naive datetime, so make it UTC-aware
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        diff = now - created_at
        seconds = diff.total_seconds()

        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            mins = int(seconds / 60)
            return f"{mins}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        else:
            days = int(seconds / 86400)
            return f"{days}d ago"

    def __repr__(self):
        return f"<Notification #{self.id} User {self.user_id}: {self.title}>"