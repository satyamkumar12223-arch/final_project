import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "students.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = str(BASE_DIR / ".flask_session")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                roll_number TEXT NOT NULL,
                marks REAL,
                attendance REAL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, roll_number)
            );
        """)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def optional_percentage(field, label):
    value = request.form.get(field, "").strip()
    if not value:
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a number.") from exc
    if not 0 <= number <= 100:
        raise ValueError(f"{label} must be between 0 and 100.")
    return number


@app.route("/")
def index():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")
        if not username or not password:
            flash("Username and password are required.", "error")
        elif len(username) > 40:
            flash("Username must be 40 characters or fewer.", "error")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
        elif password != confirmation:
            flash("The passwords do not match.", "error")
        else:
            try:
                db = get_db()
                db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                           (username, generate_password_hash(password)))
                db.commit()
                flash("Account created. You can now sign in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That username is already in use.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT id, username, password_hash FROM users WHERE username = ?",
                                (username,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Username or password is incorrect.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    students = get_db().execute(
        "SELECT id, name, roll_number, marks, attendance, created_at FROM students "
        "WHERE user_id = ? ORDER BY created_at DESC, id DESC", (session["user_id"],)
    ).fetchall()
    return render_template("dashboard.html", students=students)


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_number = request.form.get("roll_number", "").strip()
        try:
            marks = optional_percentage("marks", "Marks")
            attendance = optional_percentage("attendance", "Attendance")
            if not name or not roll_number:
                raise ValueError("Student name and roll number are required.")
            if len(name) > 100 or len(roll_number) > 30:
                raise ValueError("Name or roll number is too long.")
            db = get_db()
            db.execute("INSERT INTO students (user_id, name, roll_number, marks, attendance) "
                       "VALUES (?, ?, ?, ?, ?)",
                       (session["user_id"], name, roll_number, marks, attendance))
            db.commit()
            flash(f"{name} was added to your student list.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
        except sqlite3.IntegrityError:
            flash("That roll number is already in your list.", "error")
    return render_template("add_student.html")


@app.post("/students/<int:student_id>/delete")
@login_required
def delete_student(student_id):
    db = get_db()
    result = db.execute("DELETE FROM students WHERE id = ? AND user_id = ?",
                        (student_id, session["user_id"]))
    db.commit()
    flash("Student record deleted." if result.rowcount else "Student record was not found.",
          "success" if result.rowcount else "error")
    return redirect(url_for("dashboard"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
