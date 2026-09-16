# SmartHostel — Phase 1: Authentication + Database + Modern Layout + Dashboard

A hostel management platform that schedules room cleaning around students'
class timetables and tracks maintenance complaints from submission to
resolution.

This is **Phase 1 of 10**. It ships a real, working slice of the app:
account login/logout, password hashing, role-based sessions, a themeable
app shell, and a role-aware dashboard — end to end, UI → API → database.

## Problem statement

1. **Room cleaning** — cleaning staff often arrive while students are in
   class, so rooms stay unclean. SmartHostel will use each student's
   timetable to recommend free-period cleaning slots (Phase 4).
2. **Maintenance complaints** — students need an easy way to report and
   track issues from `Submitted → Assigned → In Progress → Resolved →
   Closed` (Phase 5).

## What's in Phase 1

- Flask app factory (`app.py`) with SQLAlchemy + SQLite
- `User` model with hashed passwords and four roles: student, cleaning
  staff, maintenance staff, admin/warden
- Session-based login via Flask-Login (`/login`, `/logout`) plus JSON
  equivalents (`/api/auth/login`, `/api/auth/logout`)
- Role-required decorator (`utils/decorators.py`) ready for role-gated
  routes in later phases
- Modern app shell: sidebar navigation, topbar, avatar chip
- **Light/dark theme system** using CSS variables, toggle in the topbar,
  preference saved in `localStorage`
- Role-aware dashboard shell with greeting, stat cards, quick actions,
  and empty states (data wiring comes in Phases 2–7)
- Toast-style flash messages, 400/401/403/404/500 error handling (JSON
  for `/api/*`, styled HTML page otherwise)
- Fully responsive layout (collapsible sidebar on mobile)
- Seed script with one demo account per role

## Technology stack

- **Frontend:** HTML5, CSS3 (custom, no framework), vanilla JS, Font Awesome
- **Backend:** Python, Flask, blueprint-based REST-style routes
- **Database:** SQLite via SQLAlchemy ORM (swap to PostgreSQL later by
  changing one env var — see below)
- **Auth:** Flask-Login sessions, Werkzeug password hashing, role field
  on the `User` model

## Project structure

```
SmartHostel/
├── app.py               # App factory, blueprint registration, error handlers
├── config.py             # Env-driven configuration
├── seed.py                # Creates one demo account per role
├── requirements.txt
├── .env.example
├── models/
│   ├── __init__.py       # Shared `db` instance
│   └── user.py            # User model + Role constants
├── routes/
│   ├── auth.py             # Login/logout (HTML + JSON API)
│   └── dashboard.py         # Role-aware dashboard route
├── utils/
│   └── decorators.py        # @role_required
├── templates/
│   ├── base.html              # Shell: sidebar, topbar, theme toggle
│   ├── _flash.html             # Toast messages
│   ├── errors.html              # Styled error page
│   ├── auth/login.html
│   └── dashboard/index.html
├── static/
│   ├── css/style.css     # Full design system (light + dark)
│   └── js/theme.js        # Theme + sidebar toggle logic
├── database/              # smarthostel.db lives here (gitignored)
└── uploads/                # Reserved for Phase 5 complaint photos
```

## Installation

```bash
cd SmartHostel
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then edit SECRET_KEY
```

## Run it

```bash
python seed.py    # creates the database + demo accounts (safe to re-run)
python app.py      # starts the dev server on http://127.0.0.1:5000
```

## Demo accounts

| Role                | Email                          | Password           |
|----------------------|----------------------------------|----------------------|
| Student               | student@smarthostel.demo        | Student@123          |
| Cleaning Staff         | cleaning@smarthostel.demo        | Cleaning@123          |
| Maintenance Staff       | maintenance@smarthostel.demo      | Maintenance@123        |
| Admin / Warden           | admin@smarthostel.demo            | Admin@123               |

These are demo-only credentials seeded locally — never used in production.

## Moving from SQLite to PostgreSQL later

Set `DATABASE_URL` in `.env`, e.g.:

```
DATABASE_URL=postgresql://user:password@localhost:5432/smarthostel
```

No other code changes are required — `config.py` reads this value directly.

## API overview (Phase 1)

| Method | Endpoint             | Description                    |
|--------|------------------------|-----------------------------------|
| POST   | `/api/auth/login`       | Log in, returns user info + role   |
| POST   | `/api/auth/logout`       | Log out the current session          |

More endpoints (`/api/timetable`, `/api/cleaning`, `/api/complaints`,
`/api/admin/*`, etc.) are added in their respective phases per the
project's full API structure.

## Security notes

- Passwords are hashed with Werkzeug's `generate_password_hash`, never
  stored in plain text.
- Sessions are HttpOnly, SameSite=Lax; `SESSION_COOKIE_SECURE` turns on
  automatically when `FLASK_ENV=production`.
- All secrets are read from `.env` (see `.env.example`) — nothing is
  hardcoded.
- 500 errors never leak stack traces to the browser; they're logged
  server-side only.

## Next up — Phase 2

Student profile page and room management (linking students to rooms,
admin room CRUD).
