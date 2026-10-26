# Student Management System

A lightweight web application for keeping student records organized. Users can create an account, sign in, and manage their own list of students through a responsive dashboard.

## Features

- Account registration with username and password confirmation
- Sign-in and sign-out with server-side sessions
- Passwords stored as Werkzeug password hashes
- Add, view, and delete student records
- Optional marks and attendance values from 0 to 100
- Student lists are scoped to the signed-in account
- Roll numbers must be unique within each account
- SQLite database created automatically on first startup
- Responsive blue and teal interface

## Technology

- **Backend:** Python, Flask, Flask-Session
- **Database:** SQLite
- **Frontend:** HTML, CSS, Jinja templates

## Project structure

```text
final_project/
├── app.py
├── students.db              # Generated at startup; local database is git-ignored
├── README.md
├── requirements.txt
├── templates/
│   ├── layout.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── add_student.html
└── static/
    └── style.css
```

## Run locally

### 1. Open the project folder

Open `final_project` in VS Code, then open a terminal from **Terminal → New Terminal**.

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate it

macOS or Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Start the application

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser. Register an account, sign in, and add student records. Stop the development server with `Ctrl+C` in the terminal.

## Main pages and routes

| Route | Access | Purpose |
| --- | --- | --- |
| `/` | Public | Redirects to sign-in or the dashboard |
| `/register` | Public | Creates a new account |
| `/login` | Public | Signs into an account |
| `/logout` | Signed in | Ends the current session |
| `/dashboard` | Signed in | Shows the current user's student records |
| `/students/add` | Signed in | Adds a student record |
| `/students/<id>/delete` | Signed in | Deletes one of the current user's records |

## Database

The app initializes `students.db` automatically and creates two tables:

- **users** — username, password hash, and account creation time
- **students** — owner account, student name, roll number, optional marks and attendance, and creation time

Each student record belongs to the account that created it. The dashboard only loads records for the signed-in account, and delete requests are also checked against that account.

## Validation and account safety

- Usernames are required, limited to 40 characters, and unique without regard to letter case.
- Passwords must contain at least 8 characters and match the confirmation field.
- Student names and roll numbers are required; marks and attendance are optional percentages between 0 and 100.
- The local SQLite database, virtual environment, and session files are excluded from Git.
- A random signing key is generated when `SECRET_KEY` is not set. Before deployment, set a persistent, randomly generated `SECRET_KEY` in the hosting environment. Use a production WSGI server and disable Flask debug mode in production.

## Current scope

The app supports account registration and sign-in plus adding, viewing, and deleting student records. Editing records, searching, filtering, and role-based access are not included.
