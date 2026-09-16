"""
Authentication routes.

/login    -> login page (GET/POST)
/register -> student registration (GET/POST)
/logout   -> ends session
/api/auth/login and /api/auth/logout -> JSON API versions
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, login_required, current_user

from models import db
from models.user import User, Role
from services.auth_service import validate_registration, register_student

auth_bp = Blueprint("auth", __name__)


def _dashboard_redirect_for(user: User) -> str:
    if user.role == Role.ADMIN:
        return url_for("admin.dashboard")
    return url_for("dashboard.index")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_redirect_for(current_user))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html"), 401

        if not user.is_active_account:
            flash("This account has been disabled. Contact the warden/admin.", "error")
            return render_template("auth/login.html"), 403

        login_user(user, remember=remember)
        next_page = request.args.get("next")
        return redirect(next_page or _dashboard_redirect_for(user))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(_dashboard_redirect_for(current_user))

    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "password": request.form.get("password"),
            "confirm_password": request.form.get("confirm_password"),
            "student_id": request.form.get("student_id"),
            "course": request.form.get("course"),
            "year": request.form.get("year"),
        }

        errors = validate_registration(data)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("auth/register.html", form_data=data), 400

        user = register_student(data)
        db.session.commit()

        flash("Registration successful! Please log in with your credentials.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form_data={})


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401

    if not user.is_active_account:
        return jsonify({"error": "This account has been disabled."}), 403

    login_user(user, remember=bool(data.get("remember")))

    return jsonify({
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
        "redirect": _dashboard_redirect_for(user),
    }), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"message": "Logged out."}), 200
