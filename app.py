"""
SmartHostel — Application entry point.

Uses the application-factory pattern so the app can be created fresh
for testing/seeding without side effects on import.
"""

import os
from flask import Flask, render_template, jsonify, request
from flask_login import LoginManager

from config import Config
from models import db
from models.user import User


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(os.path.join(app.root_path, "database"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Register Blueprints ---
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.profile import profile_bp
    from routes.room import room_bp
    from routes.timetable import timetable_bp
    from routes.cleaning import cleaning_bp
    from routes.complaints import complaint_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(cleaning_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(admin_bp)

    # --- Error handlers ---
    def _wants_json():
        return request.path.startswith("/api/") or request.accept_mimetypes["application/json"] >= request.accept_mimetypes["text/html"]

    def _error_response(code, message):
        if _wants_json():
            return jsonify({"error": message}), code
        return render_template("errors.html", code=code, message=message), code

    @app.errorhandler(400)
    def bad_request(e):
        return _error_response(400, "Bad request.")

    @app.errorhandler(401)
    def unauthorized(e):
        return _error_response(401, "You need to log in to do that.")

    @app.errorhandler(403)
    def forbidden(e):
        return _error_response(403, "You don't have permission to access this.")

    @app.errorhandler(404)
    def not_found(e):
        return _error_response(404, "That page doesn't exist.")

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Internal server error")
        return _error_response(500, "Something went wrong on our end.")

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=app.config["DEBUG"], port=5001)
