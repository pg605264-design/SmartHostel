"""
Reusable route decorators.

`role_required` protects a view so only the listed roles can reach it.
Must be stacked underneath `@login_required` (Flask-Login) so an
anonymous user is redirected to login first, before we even check role.
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in allowed_roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
