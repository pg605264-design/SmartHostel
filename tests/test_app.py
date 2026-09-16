# ============================================================
# SmartHostel - Complete Application Tests
# ============================================================

import sys
from pathlib import Path

# SmartHostel project root ko Python path mein add karo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask

from app import create_app
from config import Config
from models import db
from models.user import User, Role


# ============================================================
# Test Configuration
# ============================================================

class TestConfig(Config):
    """
    Testing ke liye real database use nahi karna hai.

    Isliye hum temporary in-memory SQLite database use kar rahe hain.
    Test complete hone ke baad database automatically disappear ho jayega.
    """

    TESTING = True

    # Real smarthostel.db ko touch nahi karega
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Testing ke time CSRF/security related complications avoid karne ke liye
    WTF_CSRF_ENABLED = False


# ============================================================
# Basic Application Tests
# ============================================================

def test_app_creation():
    """
    Check whether the Flask application can be created
    successfully without crashing.
    """

    app = create_app(TestConfig)

    assert app is not None


def test_app_testing_client():
    """
    Check whether Flask can create a test client.

    Test client browser open kiye bina website routes
    test karne deta hai.
    """

    app = create_app(TestConfig)

    client = app.test_client()

    assert client is not None


def test_404_page():
    """
    Check whether our custom 404 error handler works.
    """

    app = create_app(TestConfig)

    client = app.test_client()

    response = client.get("/this-page-does-not-exist")

    assert response.status_code == 404


# ============================================================
# Route Registration Tests
# ============================================================

EXPECTED_ROUTES = [
    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------
    "/login",
    "/register",
    "/logout",
    "/api/auth/login",
    "/api/auth/logout",

    # --------------------------------------------------------
    # Dashboard
    # --------------------------------------------------------
    "/",
    "/dashboard",

    # --------------------------------------------------------
    # Notifications
    # --------------------------------------------------------
    "/notifications/mark-read/<int:notification_id>",
    "/notifications/mark-all-read",

    # --------------------------------------------------------
    # Profile
    # --------------------------------------------------------
    "/profile",
    "/profile/edit",
    "/profile/change-password",

    # --------------------------------------------------------
    # Student Room
    # --------------------------------------------------------
    "/my-room",

    # --------------------------------------------------------
    # Timetable
    # --------------------------------------------------------
    "/timetable",
    "/timetable/add",
    "/timetable/<int:entry_id>/delete",

    # --------------------------------------------------------
    # Cleaning
    # --------------------------------------------------------
    "/cleaning",
    "/cleaning/request",
    "/cleaning/<int:request_id>/update-status",

    # --------------------------------------------------------
    # Complaints
    # --------------------------------------------------------
    "/complaints",
    "/complaints/raise",
    "/complaints/<int:complaint_id>",
    "/complaints/<int:complaint_id>/update-status",

    # --------------------------------------------------------
    # Admin
    # --------------------------------------------------------
    "/admin/",
    "/admin/students",
    "/admin/students/<int:student_id>",
    "/admin/students/<int:student_id>/toggle-active",
    "/admin/students/<int:student_id>/assign-room",
    "/admin/students/<int:student_id>/remove-room",
    "/admin/rooms",
    "/admin/rooms/create",
    "/admin/rooms/<int:room_id>",
    "/admin/rooms/<int:room_id>/edit",
    "/admin/rooms/<int:room_id>/assign",
    "/admin/rooms/<int:room_id>/remove-student",
]


def test_all_expected_routes_are_registered():
    """
    Check whether all important SmartHostel routes
    are registered in the Flask application.
    """

    app = create_app(TestConfig)

    registered_routes = {
        rule.rule
        for rule in app.url_map.iter_rules()
    }

    missing_routes = [
        route
        for route in EXPECTED_ROUTES
        if route not in registered_routes
    ]

    assert not missing_routes, (
        "These routes are missing:\n"
        + "\n".join(missing_routes)
    )


# ============================================================
# Login Protection Tests
# ============================================================

PROTECTED_ROUTES = [
    "/dashboard",
    "/profile",
    "/profile/edit",
    "/my-room",
    "/timetable",
    "/cleaning",
    "/cleaning/request",
    "/complaints",
    "/complaints/raise",
]


def test_protected_pages_require_login():
    """
    Check that important SmartHostel pages cannot be
    accessed without logging in.
    """

    app = create_app(TestConfig)

    client = app.test_client()

    for route in PROTECTED_ROUTES:

        response = client.get(route)

        # Flask-Login unauthenticated user ko
        # login page par redirect karna chahiye.
        assert response.status_code == 302, (
            f"{route} is not protected correctly."
        )

        assert "/login" in response.location, (
            f"{route} does not redirect to the login page."
        )


# ============================================================
# Helper: Create Test User
# ============================================================

def create_test_user(role, email):
    """
    Testing database mein temporary user create karta hai.

    Ye user real SmartHostel database mein create nahi hota.
    """

    user = User(
        name=f"Test {role}",
        email=email,
        role=role,
        phone="9999999999",
        is_active_account=True
    )

    user.set_password("password123")

    db.session.add(user)
    db.session.commit()

    return user


# ============================================================
# Helper: Login Test User
# ============================================================

def login_test_user(client, email):
    """
    Test client ke through user ko login karta hai.
    """

    return client.post(
        "/login",
        data={
            "email": email,
            "password": "password123"
        },
        follow_redirects=False
    )


# ============================================================
# Role Based Access Tests
# ============================================================

def test_student_cannot_access_admin_dashboard():
    """
    Check that a student cannot access
    the admin dashboard.
    """

    app = create_app(TestConfig)

    with app.app_context():

        # Testing database mein tables create karo
        db.create_all()

        student = create_test_user(
            Role.STUDENT,
            "student@test.com"
        )

        client = app.test_client()

        # Student login
        login_response = login_test_user(
            client,
            student.email
        )

        assert login_response.status_code == 302

        # Student admin dashboard access karne ki koshish karta hai
        response = client.get("/admin/")

        # Student ko permission nahi milni chahiye
        assert response.status_code in [302, 403]


def test_admin_can_access_admin_dashboard():
    """
    Check that an admin can access
    the admin dashboard.
    """

    app = create_app(TestConfig)

    with app.app_context():

        # Testing database mein tables create karo
        db.create_all()

        admin = create_test_user(
            Role.ADMIN,
            "admin@test.com"
        )

        client = app.test_client()

        # Admin login
        login_response = login_test_user(
            client,
            admin.email
        )

        assert login_response.status_code == 302

        # Admin dashboard access
        response = client.get("/admin/")

        # Admin ko dashboard access milna chahiye
        assert response.status_code == 200

# ============================================================
# SmartHostel - Complaint Workflow Tests
# ============================================================

from models.complaint import Complaint, ComplaintStatus
from models.notification import Notification


def test_student_can_raise_complaint():
    """
    Check complete complaint creation workflow.

    Test karega:
    1. Student login kar sakta hai
    2. Student complaint submit kar sakta hai
    3. Complaint database mein save hoti hai
    4. Complaint ka status Pending hota hai
    5. Student ke liye notification create hoti hai
    """

    app = create_app(TestConfig)

    with app.app_context():

        # Testing database ke tables create karo
        db.create_all()

        # Test student create karo
        student = create_test_user(
            Role.STUDENT,
            "complaint_student@test.com"
        )

        client = app.test_client()

        # Student login
        login_response = login_test_user(
            client,
            student.email
        )

        assert login_response.status_code == 302

        # Complaint submit karo
        response = client.post(
            "/complaints/raise",
            data={
                "category": "Electrical",
                "title": "Study Lamp Not Working",
                "description": "The study lamp is not working properly."
            },
            follow_redirects=False
        )

        # Successful submission dashboard par redirect honi chahiye
        assert response.status_code == 302

        # Complaint database mein save hui hai ya nahi
        complaint = Complaint.query.filter_by(
            student_id=student.id
        ).first()

        assert complaint is not None

        # Complaint ki details verify karo
        assert complaint.category == "Electrical"
        assert complaint.title == "Study Lamp Not Working"
        assert complaint.description == (
            "The study lamp is not working properly."
        )

        # New complaint ka default status Pending hona chahiye
        assert complaint.status == ComplaintStatus.PENDING

        # Notification create hui hai ya nahi
        notification = Notification.query.filter_by(
            user_id=student.id
        ).first()

        assert notification is not None

        assert notification.title == (
            f"Complaint #{complaint.id} Filed"
        )

        assert notification.user_id == student.id

# ============================================================
# SmartHostel - Complaint Status Update Test
# ============================================================

def test_admin_can_update_complaint_status():
    """
    Check complete complaint status update workflow.

    Test karega:
    1. Student complaint create karta hai
    2. Admin login karta hai
    3. Admin complaint ko In Progress karta hai
    4. Resolution notes save hoti hain
    5. Student ke liye update notification create hoti hai
    """

    app = create_app(TestConfig)

    with app.app_context():

        # Testing database ke tables create karo
        db.create_all()

        # ----------------------------------------------------
        # Student create karo
        # ----------------------------------------------------
        student = create_test_user(
            Role.STUDENT,
            "status_student@test.com"
        )

        # ----------------------------------------------------
        # Admin create karo
        # ----------------------------------------------------
        admin = create_test_user(
            Role.ADMIN,
            "status_admin@test.com"
        )

        # ----------------------------------------------------
        # Student ke liye complaint directly create karo
        # ----------------------------------------------------
        complaint = Complaint(
            student_id=student.id,
            category="Plumbing",
            title="Bathroom Tap Leaking",
            description="The bathroom tap is continuously leaking.",
            status=ComplaintStatus.PENDING
        )

        db.session.add(complaint)
        db.session.commit()

        complaint_id = complaint.id

        # ----------------------------------------------------
        # Admin client create karo
        # ----------------------------------------------------
        client = app.test_client()

        # Admin login
        login_response = login_test_user(
            client,
            admin.email
        )

        assert login_response.status_code == 302

        # ----------------------------------------------------
        # Admin complaint status update karega
        # ----------------------------------------------------
        response = client.post(
            f"/complaints/{complaint_id}/update-status",
            data={
                "status": ComplaintStatus.IN_PROGRESS,
                "resolution_notes": "Maintenance team is checking the tap."
            },
            follow_redirects=False
        )

        # Successful update ke baad complaint detail par redirect
        assert response.status_code == 302

        # ----------------------------------------------------
        # Database se complaint dobara load karo
        # ----------------------------------------------------
        updated_complaint = db.session.get(
            Complaint,
            complaint_id
        )

        assert updated_complaint is not None

        # Status correctly update hua
        assert updated_complaint.status == ComplaintStatus.IN_PROGRESS

        # Resolution notes correctly save hui
        assert updated_complaint.resolution_notes == (
            "Maintenance team is checking the tap."
        )

        # ----------------------------------------------------
        # Student notification verify karo
        # ----------------------------------------------------
        notifications = Notification.query.filter_by(
            user_id=student.id
        ).all()

        # At least one notification honi chahiye
        assert len(notifications) >= 1

        # Latest notification check karo
        notification = notifications[-1]

        assert notification.user_id == student.id

        assert notification.title == (
            f"Complaint #{complaint_id} {ComplaintStatus.IN_PROGRESS}"
        )

# ============================================================
# SmartHostel - Cleaning Request Workflow Test
# ============================================================

from models.cleaning import CleaningRequest, CleaningStatus


def test_student_can_request_cleaning():
    """
    Check complete cleaning request workflow.

    Test karega:
    1. Student login karta hai
    2. Cleaning request submit karta hai
    3. Request database mein save hoti hai
    4. Default status Pending hota hai
    5. Student ke liye notification create hoti hai
    """

    app = create_app(TestConfig)

    with app.app_context():

        # Testing database ke tables create karo
        db.create_all()

        # ----------------------------------------------------
        # Student create karo
        # ----------------------------------------------------
        student = create_test_user(
            Role.STUDENT,
            "cleaning_student@test.com"
        )

        # ----------------------------------------------------
        # Test client create karo
        # ----------------------------------------------------
        client = app.test_client()

        # Student login
        login_response = login_test_user(
            client,
            student.email
        )

        assert login_response.status_code == 302

        # ----------------------------------------------------
        # Cleaning request submit karo
        # ----------------------------------------------------
        response = client.post(
            "/cleaning/request",
            data={
                "preferred_date": "2026-09-20",
                "preferred_slot": "10:00 AM - 11:00 AM",
                "notes": "Please clean the room properly."
            },
            follow_redirects=False
        )

        # Successful request ke baad dashboard par redirect
        assert response.status_code == 302

        # ----------------------------------------------------
        # Database mein cleaning request check karo
        # ----------------------------------------------------
        cleaning_request = CleaningRequest.query.filter_by(
            student_id=student.id
        ).first()

        assert cleaning_request is not None

        # Request ki details verify karo
        assert cleaning_request.preferred_date == "2026-09-20"

        assert cleaning_request.preferred_slot == (
            "10:00 AM - 11:00 AM"
        )

        assert cleaning_request.notes == (
            "Please clean the room properly."
        )

        # New request ka default status Pending hona chahiye
        assert cleaning_request.status == CleaningStatus.PENDING

        # ----------------------------------------------------
        # Notification verify karo
        # ----------------------------------------------------
        notification = Notification.query.filter_by(
            user_id=student.id
        ).first()

        assert notification is not None

        assert notification.title == (
            "Cleaning Request Submitted"
        )

        assert notification.user_id == student.id

        assert "2026-09-20" in notification.message

        assert "10:00 AM - 11:00 AM" in notification.message

# ============================================================
# SmartHostel - Cleaning Staff Status Update Test
# ============================================================

def test_cleaning_staff_can_update_cleaning_status():
    """
    Check complete cleaning staff workflow.

    Test karega:
    1. Student cleaning request create karta hai
    2. Cleaning staff login karta hai
    3. Staff request ka status update karta hai
    4. Staff automatically assigned hota hai
    5. Student ko notification milti hai
    """

    app = create_app(TestConfig)

    with app.app_context():

        # Testing database ke tables create karo
        db.create_all()

        # ----------------------------------------------------
        # Student create karo
        # ----------------------------------------------------
        student = create_test_user(
            Role.STUDENT,
            "cleaning_status_student@test.com"
        )

        # ----------------------------------------------------
        # Cleaning staff create karo
        # ----------------------------------------------------
        cleaning_staff = create_test_user(
            Role.CLEANING_STAFF,
            "cleaning_staff@test.com"
        )

        # ----------------------------------------------------
        # Cleaning request directly create karo
        # ----------------------------------------------------
        cleaning_request = CleaningRequest(
            student_id=student.id,
            preferred_date="2026-09-21",
            preferred_slot="11:00 AM - 12:00 PM",
            notes="Please clean the room.",
            status=CleaningStatus.PENDING
        )

        db.session.add(cleaning_request)
        db.session.commit()

        request_id = cleaning_request.id

        # ----------------------------------------------------
        # Test client create karo
        # ----------------------------------------------------
        client = app.test_client()

        # Cleaning staff login
        login_response = login_test_user(
            client,
            cleaning_staff.email
        )

        assert login_response.status_code == 302

        # ----------------------------------------------------
        # Cleaning staff status update karega
        # ----------------------------------------------------
        response = client.post(
            f"/cleaning/{request_id}/update-status",
            data={
                "status": CleaningStatus.IN_PROGRESS
            },
            follow_redirects=False
        )

        # Successful update ke baad cleaning page par redirect
        assert response.status_code == 302

        # ----------------------------------------------------
        # Database se request dobara load karo
        # ----------------------------------------------------
        updated_request = db.session.get(
            CleaningRequest,
            request_id
        )

        assert updated_request is not None

        # Status correctly update hua
        assert updated_request.status == CleaningStatus.IN_PROGRESS

        # Cleaning staff automatically assigned hona chahiye
        assert updated_request.assigned_staff_id == cleaning_staff.id

        # ----------------------------------------------------
        # Student notification verify karo
        # ----------------------------------------------------
        notifications = Notification.query.filter_by(
            user_id=student.id
        ).all()

        assert len(notifications) >= 1

        # Latest notification check karo
        notification = notifications[-1]

        assert notification.user_id == student.id

        assert notification.title == (
            f"Cleaning Request {CleaningStatus.IN_PROGRESS}"
        )

        assert "2026-09-21" in notification.message

        assert CleaningStatus.IN_PROGRESS in notification.message

# ============================================================
# SmartHostel - Timetable Workflow Test
# ============================================================

from models.timetable import Timetable


def test_admin_can_add_timetable_entry():
    """
    Check complete timetable creation workflow.

    Test karega:
    1. Admin login karta hai
    2. Admin new class add karta hai
    3. Timetable entry database mein save hoti hai
    4. Saari class details correctly save hoti hain
    5. Timetable page successfully open hota hai
    """

    app = create_app(TestConfig)

    with app.app_context():

        # Testing database ke tables create karo
        db.create_all()

        # ----------------------------------------------------
        # Admin create karo
        # ----------------------------------------------------
        admin = create_test_user(
            Role.ADMIN,
            "timetable_admin@test.com"
        )

        # ----------------------------------------------------
        # Test client create karo
        # ----------------------------------------------------
        client = app.test_client()

        # Admin login
        login_response = login_test_user(
            client,
            admin.email
        )

        assert login_response.status_code == 302

        # ----------------------------------------------------
        # New timetable class add karo
        # ----------------------------------------------------
        response = client.post(
            "/timetable/add",
            data={
                "day": "Monday",
                "subject": "Data Structures",
                "start_time": "09:00 AM",
                "end_time": "10:30 AM",
                "room_number": "LH-101",
                "faculty": "Dr. Gupta"
            },
            follow_redirects=False
        )

        # Successful submission ke baad timetable page par redirect
        assert response.status_code == 302

        # ----------------------------------------------------
        # Database mein timetable entry check karo
        # ----------------------------------------------------
        timetable = Timetable.query.filter_by(
            subject="Data Structures"
        ).first()

        assert timetable is not None

        # ----------------------------------------------------
        # Timetable details verify karo
        # ----------------------------------------------------
        assert timetable.day == "Monday"

        assert timetable.subject == "Data Structures"

        assert timetable.start_time == "09:00 AM"

        assert timetable.end_time == "10:30 AM"

        assert timetable.room_number == "LH-101"

        assert timetable.faculty == "Dr. Gupta"

        # ----------------------------------------------------
        # Timetable page open karke verify karo
        # ----------------------------------------------------
        page_response = client.get("/timetable")

        assert page_response.status_code == 200

        # Added subject page ke response mein hona chahiye
        assert b"Data Structures" in page_response.data


def test_student_cannot_delete_timetable():
    app = create_app()

    with app.app_context():
        db.create_all()

        # Agar ye test user pehle se database mein hai,
        # to usse delete karo taaki UNIQUE email error na aaye.
        old_user = User.query.filter_by(
            email="timetable_student@test.com"
        ).first()

        if old_user:
            db.session.delete(old_user)
            db.session.commit()

        student = create_test_user(
            Role.STUDENT,
            "timetable_student@test.com"
        )

        client = app.test_client()

        login_test_user(client, student.email)

        response = client.post(
            "/timetable/1/delete"
        )

        assert response.status_code in [302, 403]

def test_admin_can_delete_timetable():
    app = create_app()

    with app.app_context():
        db.create_all()

        old_admin = User.query.filter_by(
            email="delete_admin@test.com"
        ).first()

        if old_admin:
            db.session.delete(old_admin)
            db.session.commit()

        admin = create_test_user(
            Role.ADMIN,
            "delete_admin@test.com"
        )

        timetable = Timetable(
            day="Monday",
            subject="Delete Test",
            start_time="09:00 AM",
            end_time="10:00 AM",
            room_number="LH-101",
            faculty="Dr. Gupta"
        )

        db.session.add(timetable)
        db.session.commit()

        timetable_id = timetable.id

        client = app.test_client()

        login_test_user(client, admin.email)

        response = client.post(
            f"/timetable/{timetable_id}/delete"
        )

        assert response.status_code == 302

        deleted = db.session.get(
            Timetable,
            timetable_id
        )

        assert deleted is None

def test_student_can_update_profile():
    app = create_app()

    with app.app_context():
        db.create_all()

        old_user = User.query.filter_by(
            email="profile_student@test.com"
        ).first()

        if old_user:
            db.session.delete(old_user)
            db.session.commit()

        student = create_test_user(
            Role.STUDENT,
            "profile_student@test.com"
        )

        client = app.test_client()

        login_test_user(client, student.email)

        response = client.post(
            "/profile/edit",
            data={
                "name": "Updated Student",
                "email": "profile_student@test.com",
                "phone": "8888888888",
                "course": "Computer Science",
                "year": "2"
            },
            follow_redirects=False
        )

        assert response.status_code == 302

        updated_user = db.session.get(
            User,
            student.id
        )

        assert updated_user.name == "Updated Student"
        assert updated_user.phone == "8888888888"

def test_student_can_change_password():
    app = create_app()

    with app.app_context():
        db.create_all()

        old_user = User.query.filter_by(
            email="password_student@test.com"
        ).first()

        if old_user:
            db.session.delete(old_user)
            db.session.commit()

        student = create_test_user(
            Role.STUDENT,
            "password_student@test.com"
        )

        client = app.test_client()

        login_test_user(client, student.email)

        response = client.post(
            "/profile/change-password",
            data={
                "current_password": "password123",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            },
            follow_redirects=False
        )

        assert response.status_code == 302

        updated_user = db.session.get(
            User,
            student.id
        )

        assert updated_user.check_password("NewPassword123!")