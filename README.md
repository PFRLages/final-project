# English Passion – School Management System

A role-based web application for an online English teaching school, replacing manual
Google Drive/Sheets workflows. It provides user management, class scheduling, attendance
recording, automated monthly reports, payment tracking, holiday management and an eBook library.

## Technology Stack
- **Frontend:** React 19 + Vite, Bootstrap 5, Axios
- **Backend:** FastAPI (Python), Motor (async MongoDB driver)
- **Database:** MongoDB
- **Auth:** JWT (JSON Web Tokens) with bcrypt password hashing

## Roles
- **management** – full administrative access (users, students, payments, holidays, eBooks)
- **teacher** – schedules, attendance, monthly reports, shared eBooks
- **student** – own schedule, reports, attendance, payments and shared eBooks

---

## Prerequisites
- **Python 3.11+**
- **Node.js 18+** (with npm)
- **MongoDB** running locally (default: `mongodb://localhost:27017`)

---

## 1. Backend Setup

```bash
cd backend
python -m venv venv

# Activate the virtual environment:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# English Passion – School Management System

A role-based web application for an online English teaching school, replacing manual
Google Drive/Sheets workflows. It provides user management, class scheduling, attendance
recording, automated monthly reports, payment tracking, holiday management and an eBook library.

## Technology Stack
- **Frontend:** React 19 + Vite, Bootstrap 5, Axios
- **Backend:** FastAPI (Python), Motor (async MongoDB driver)
- **Database:** MongoDB
- **Auth:** JWT (JSON Web Tokens) with bcrypt password hashing

## Roles
- **management** – full administrative access (users, students, payments, holidays, eBooks)
- **teacher** – schedules, attendance, monthly reports, shared eBooks
- **student** – own schedule, reports, attendance, payments and shared eBooks

---

## Prerequisites
- **Python 3.11+**
- **Node.js 18+** (with npm)
- **MongoDB** running locally (default: `mongodb://localhost:27017`)

---

## 1. Backend Setup

```bash
cd backend
python -m venv venv

# Activate the virtual environment:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
Create a file backend/.env with the following:

MONGO_URL=mongodb://localhost:27017
DB_NAME=ep_school
JWT_SECRET=change-this-to-any-long-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_EMAIL=admin@ep.com
ADMIN_PASSWORD=test26
Seed the database (creates all accounts)
With MongoDB running and the virtual environment active:

python reset_db.py
This clears the database and creates:

Role	Email	Password
Management	admin@ep.com	test26
Teacher	kristin@ep.com	test26
Teacher	mai@ep.com	test26
Student	lucas@ep.com	test26
Student	kana@ep.com	test26
Run the backend
uvicorn main:app --reload --port 8000
The API runs at http://127.0.0.1:8000. Interactive API docs are available at http://127.0.0.1:8000/docs. Uploaded eBooks are served from http://127.0.0.1:8000/uploads/....

2. Frontend Setup
cd frontend
npm install
Create a file frontend/.env with:

VITE_API_URL=http://127.0.0.1:8000
Run the frontend
npm run dev
The app runs at http://localhost:5173. Open it in a browser and log in with one of the accounts above.

Notes
The backend must be running before using the frontend.
eBooks are stored on disk in backend/uploads/, organised into folders by level. reset_db.py automatically imports any PDFs already in that folder.
Holidays are not seeded automatically; upload them per country from the management Holidays page (CSV/Excel), then generate a student's monthly report.
Project Structure
backend/
  main.py            # FastAPI app entry point
  database.py        # MongoDB connection + indexes
  reset_db.py        # Reset & seed script
  requirements.txt
  core/              # security (auth, RBAC), seeding, statuses
  models/            # Pydantic schemas
  routers/           # API endpoints per feature
  uploads/           # eBook PDFs (organised by level)
frontend/
  src/
    api/             # Axios client
    context/         # Auth context
    components/      # Layout, ProtectedRoute
    pages/           # Role-based dashboards & management screens