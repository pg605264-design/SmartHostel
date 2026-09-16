"""
Room routes — student's 'My Room' page.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models.user import Role
from utils.decorators import role_required

room_bp = Blueprint("room", __name__)


@room_bp.route("/my-room")
@login_required
def my_room():
    profile = current_user.profile
    room = profile.room if profile else None
    occupants = []
    if room:
        occupants = [p for p in room.occupants.all()]
    return render_template("room/index.html", profile=profile, room=room, occupants=occupants)
