import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "24aa0c9b83bb3b3f8be1a8d38c79b591"


# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")


def create_users_table():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_dsa_table():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dsa_problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            topic TEXT,
            problem TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()
# -----------------------------------------


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        try:
            hashed_password = generate_password_hash(password)

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )

            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists", "danger")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route('/dsa')
def dsa():
    return render_template('dsa.html')

@app.route('/aptitude')
def aptitude():
    return "<h2>Aptitude - Coming Soon</h2>"

@app.route('/core')
def core():
    return "<h2>Core Subjects - Coming Soon</h2>"

@app.route('/mock')
def mock():
    return "<h2>Mock Tests - Coming Soon</h2>"

@app.route('/progress')
def progress():
    return "<h2>Progress Page - Coming Soon</h2>"

@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, topic, problem, status FROM dsa_problems WHERE username = ?",
        (session['user'],)
    )
    problems = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM dsa_problems WHERE username = ?",
        (session['user'],)
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM dsa_problems WHERE username = ? AND status = 'Solved'",
        (session['user'],)
    )
    solved = cursor.fetchone()[0]

    conn.close()

    percent = int((solved / total) * 100) if total > 0 else 0

    return render_template(
        "dashboard.html",
        problems=problems,
        total=total,
        solved=solved,
        percent=percent
    )


@app.route("/toggle_status/<int:problem_id>")
def toggle_status(problem_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT status FROM dsa_problems WHERE id=? AND username=?",
        (problem_id, session['user'])
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return redirect(url_for("dashboard"))

    new_status = "Solved" if row[0] == "Unsolved" else "Unsolved"

    cursor.execute(
        "UPDATE dsa_problems SET status=? WHERE id=? AND username=?",
        (new_status, problem_id, session['user'])
    )

    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))




@app.route("/add_problem", methods=["POST"])
def add_problem():
    if 'user' not in session:
        return redirect(url_for('login'))

    topic = request.form['topic']
    problem = request.form['problem']
    username = session['user']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO dsa_problems (username, topic, problem, status)
        VALUES (?, ?, ?, ?)
        """,
        (username, topic, problem, "Unsolved")
    )

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route("/update_status/<int:id>")
def update_status(id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE dsa SET status='Solved' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/delete_problem/<int:problem_id>")
def delete_problem(problem_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM dsa_problems WHERE id=? AND username=?",
        (problem_id, session['user'])
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))



create_users_table()
create_dsa_table()

if __name__ == "__main__":
    app.run(debug=True)

