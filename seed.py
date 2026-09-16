"""
Seed the database with rich demo data for all roles, rooms, timetables, cleanings, and complaints.

Run with:  python seed.py
"""

from app import create_app
from models import db
from models.user import User, Role
from models.room import Room, RoomStatus, RoomType
from models.student_profile import StudentProfile
from models.timetable import Timetable
from models.cleaning import CleaningRequest, CleaningStatus
from models.complaint import Complaint, ComplaintStatus, ComplaintCategory

DEMO_USERS = [
    {"name": "Prashant Kumar", "email": "student@smarthostel.demo", "password": "Student@123", "role": Role.STUDENT, "phone": "9876543210"},
    {"name": "Rahul Verma", "email": "student2@smarthostel.demo", "password": "Student@123", "role": Role.STUDENT, "phone": "9876543211"},
    {"name": "Meena Devi", "email": "cleaning@smarthostel.demo", "password": "Cleaning@123", "role": Role.CLEANING_STAFF, "phone": "9876543212"},
    {"name": "Ravi Shankar", "email": "maintenance@smarthostel.demo", "password": "Maintenance@123", "role": Role.MAINTENANCE_STAFF, "phone": "9876543213"},
    {"name": "Dr. Anjali Sharma", "email": "admin@smarthostel.demo", "password": "Admin@123", "role": Role.ADMIN, "phone": "9876543214"},
]

DEMO_ROOMS = [
    {"hostel": "Boys Hostel", "block": "B", "floor": 2, "room_number": "204", "room_type": RoomType.DOUBLE, "capacity": 2, "status": RoomStatus.OCCUPIED},
    {"hostel": "Boys Hostel", "block": "B", "floor": 2, "room_number": "205", "room_type": RoomType.DOUBLE, "capacity": 2, "status": RoomStatus.AVAILABLE},
    {"hostel": "Girls Hostel", "block": "A", "floor": 1, "room_number": "101", "room_type": RoomType.SINGLE, "capacity": 1, "status": RoomStatus.AVAILABLE},
    {"hostel": "Girls Hostel", "block": "A", "floor": 1, "room_number": "102", "room_type": RoomType.TRIPLE, "capacity": 3, "status": RoomStatus.AVAILABLE},
]


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Seed Users
        users_by_email = {}
        for entry in DEMO_USERS:
            user = User.query.filter_by(email=entry["email"]).first()
            if not user:
                user = User(name=entry["name"], email=entry["email"], role=entry["role"], phone=entry["phone"])
                user.set_password(entry["password"])
                db.session.add(user)
                db.session.flush()
            users_by_email[entry["email"]] = user

        # Seed Rooms
        rooms_by_number = {}
        for r_data in DEMO_ROOMS:
            room = Room.query.filter_by(hostel=r_data["hostel"], block=r_data["block"], room_number=r_data["room_number"]).first()
            if not room:
                room = Room(**r_data)
                db.session.add(room)
                db.session.flush()
            rooms_by_number[f"{r_data['block']}-{r_data['room_number']}"] = room

        # Seed Student Profiles
        student_user = users_by_email.get("student@smarthostel.demo")
        room_b204 = rooms_by_number.get("B-204")
        if student_user:
            profile = StudentProfile.query.filter_by(user_id=student_user.id).first()
            if not profile:
                profile = StudentProfile(
                    user_id=student_user.id,
                    student_id="STU-2024-001",
                    course="Computer Science",
                    year=3,
                    hostel="Boys Hostel",
                    block="B",
                    room_id=room_b204.id if room_b204 else None
                )
                db.session.add(profile)

        student2_user = users_by_email.get("student2@smarthostel.demo")
        if student2_user:
            profile2 = StudentProfile.query.filter_by(user_id=student2_user.id).first()
            if not profile2:
                profile2 = StudentProfile(
                    user_id=student2_user.id,
                    student_id="STU-2024-002",
                    course="Computer Science",
                    year=3,
                    hostel="Boys Hostel",
                    block="B",
                    room_id=room_b204.id if room_b204 else None
                )
                db.session.add(profile2)

        # Update room auto status
        if room_b204:
            room_b204.auto_update_status()

        # Seed Timetable
        if Timetable.query.count() == 0:
            timetables = [
                Timetable(day="Monday", subject="Data Structures & Algorithms", start_time="09:00 AM", end_time="10:30 AM", room_number="LH-101", faculty="Dr. Gupta", course="Computer Science", year=3),
                Timetable(day="Monday", subject="Database Management Systems", start_time="11:00 AM", end_time="12:30 PM", room_number="LH-102", faculty="Prof. Roy", course="Computer Science", year=3),
                Timetable(day="Tuesday", subject="Operating Systems", start_time="10:00 AM", end_time="11:30 AM", room_number="LH-201", faculty="Dr. Verma", course="Computer Science", year=3),
                Timetable(day="Wednesday", subject="Computer Networks", start_time="09:00 AM", end_time="10:30 AM", room_number="LH-103", faculty="Dr. Sharma", course="Computer Science", year=3),
                Timetable(day="Thursday", subject="Software Engineering", start_time="02:00 PM", end_time="03:30 PM", room_number="Lab-2", faculty="Prof. Mehta", course="Computer Science", year=3),
                Timetable(day="Friday", subject="Web Technologies Lab", start_time="10:00 AM", end_time="01:00 PM", room_number="Lab-1", faculty="Dr. Gupta", course="Computer Science", year=3),
            ]
            db.session.add_all(timetables)

        # Seed Cleaning Requests
        cleaner_user = users_by_email.get("cleaning@smarthostel.demo")
        if CleaningRequest.query.count() == 0 and student_user:
            req1 = CleaningRequest(
                student_id=student_user.id,
                room_id=room_b204.id if room_b204 else None,
                preferred_date="2026-09-08",
                preferred_slot="10:00 AM - 11:00 AM",
                notes="Please mop the floor and clear dust near window.",
                status=CleaningStatus.SCHEDULED,
                assigned_staff_id=cleaner_user.id if cleaner_user else None
            )
            req2 = CleaningRequest(
                student_id=student_user.id,
                room_id=room_b204.id if room_b204 else None,
                preferred_date="2026-09-01",
                preferred_slot="02:00 PM - 03:00 PM",
                notes="Regular cleaning",
                status=CleaningStatus.COMPLETED,
                assigned_staff_id=cleaner_user.id if cleaner_user else None
            )
            db.session.add_all([req1, req2])

        # Seed Complaints
        maint_user = users_by_email.get("maintenance@smarthostel.demo")
        if Complaint.query.count() == 0 and student_user:
            c1 = Complaint(
                student_id=student_user.id,
                category=ComplaintCategory.PLUMBING,
                title="Bathroom Tap Leaking",
                description="The washroom faucet in B-204 is continuously dripping water.",
                status=ComplaintStatus.IN_PROGRESS,
                assigned_staff_id=maint_user.id if maint_user else None,
                resolution_notes="Inspected tap washer. Replacement ordered."
            )
            c2 = Complaint(
                student_id=student_user.id,
                category=ComplaintCategory.INTERNET,
                title="Wi-Fi Router Disconnected",
                description="Wi-Fi signal on 2nd floor Block B is dropping repeatedly.",
                status=ComplaintStatus.RESOLVED,
                assigned_staff_id=maint_user.id if maint_user else None,
                resolution_notes="Restarted access point and re-terminated Ethernet connector."
            )
            db.session.add_all([c1, c2])

        db.session.commit()
        print("Database seed completed successfully with rich demo data!")


if __name__ == "__main__":
    seed()
