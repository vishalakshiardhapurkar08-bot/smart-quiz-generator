from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "smart-quiz-secret-key"
DB = "database.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student'
    );

    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        topic TEXT NOT NULL,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        answer TEXT NOT NULL,
        difficulty TEXT NOT NULL DEFAULT 'Medium'
    );

    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        topic TEXT NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    admin = conn.execute("SELECT id FROM users WHERE email=?", ("admin@quiz.com",)).fetchone()
    if not admin:
        conn.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                     ("Administrator", "admin@quiz.com", "admin123", "admin"))
    count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    if count == 0:
        sample = [
            ("Operating System","Basics","Which component manages computer hardware and software resources?","Operating System","Compiler","Browser","Database","A","Easy"),
            ("Operating System","Basics","Which scheduling algorithm uses a fixed time quantum?","FCFS","SJF","Round Robin","Priority","C","Easy"),
            ("Computer Network","Basics","What does IP stand for?","Internet Protocol","Internal Process","Input Program","Internet Program","A","Easy"),
            ("Python","Basics","Which keyword is used to define a function in Python?","func","define","def","function","C","Easy"),
            ("Database","SQL","Which command is used to retrieve data from a database?","GET","SELECT","FETCHALL","READ","B","Easy")
        ]
        conn.executemany("""INSERT INTO questions
        (subject,topic,question,option_a,option_b,option_c,option_d,answer,difficulty)
        VALUES (?,?,?,?,?,?,?,?,?)""", sample)
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        try:
            conn.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                         (name,email,password))
            conn.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?",
                            (email,password)).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    subjects = conn.execute("SELECT DISTINCT subject FROM questions ORDER BY subject").fetchall()
    results = conn.execute("""SELECT * FROM results WHERE user_id=?
                              ORDER BY created_at DESC LIMIT 5""",
                           (session["user_id"],)).fetchall()
    conn.close()
    return render_template("dashboard.html", subjects=subjects, results=results)

@app.route("/quiz", methods=["GET","POST"])
@login_required
def quiz():
    subject = request.values.get("subject", "")
    topic = request.values.get("topic", "")
    difficulty = request.values.get("difficulty", "All")
    conn = get_db()
    topics = conn.execute("SELECT DISTINCT topic FROM questions WHERE subject=? ORDER BY topic",
                          (subject,)).fetchall() if subject else []
    if request.method == "POST":
        query = "SELECT * FROM questions WHERE subject=?"
        params = [subject]
        if topic:
            query += " AND topic=?"; params.append(topic)
        if difficulty != "All":
            query += " AND difficulty=?"; params.append(difficulty)
        query += " ORDER BY RANDOM() LIMIT 10"
        questions = conn.execute(query, params).fetchall()
        conn.close()
        if not questions:
            flash("No questions found for this selection.", "error")
            return redirect(url_for("dashboard"))
        return render_template("quiz.html", questions=questions, subject=subject, topic=topic)
    conn.close()
    return render_template("quiz_select.html", subjects=conn.execute("SELECT DISTINCT subject FROM questions").fetchall() if False else [])

@app.route("/start_quiz", methods=["POST"])
@login_required
def start_quiz():
    subject = request.form["subject"]
    topic = request.form.get("topic","")
    difficulty = request.form.get("difficulty","All")
    conn = get_db()
    query = "SELECT * FROM questions WHERE subject=?"
    params=[subject]
    if topic:
        query += " AND topic=?"; params.append(topic)
    if difficulty != "All":
        query += " AND difficulty=?"; params.append(difficulty)
    query += " ORDER BY RANDOM() LIMIT 10"
    questions = conn.execute(query, params).fetchall()
    conn.close()
    if not questions:
        flash("No questions found.", "error")
        return redirect(url_for("dashboard"))
    return render_template("quiz.html", questions=questions, subject=subject, topic=topic)

@app.route("/submit_quiz", methods=["POST"])
@login_required
def submit_quiz():
    subject = request.form["subject"]
    topic = request.form.get("topic","")
    ids = request.form.get("question_ids","").split(",")
    conn = get_db()
    score = 0
    total = 0
    review = []
    for qid in ids:
        if not qid: continue
        q = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
        if not q: continue
        total += 1
        selected = request.form.get(f"q_{qid}", "")
        correct = selected == q["answer"]
        if correct: score += 1
        review.append((q, selected, correct))
    conn.execute("INSERT INTO results(user_id,subject,topic,score,total) VALUES(?,?,?,?,?)",
                 (session["user_id"],subject,topic,score,total))
    conn.commit(); conn.close()
    return render_template("result.html", score=score, total=total, review=review)

@app.route("/admin")
@login_required
@admin_required
def admin():
    conn = get_db()
    questions = conn.execute("SELECT * FROM questions ORDER BY id DESC").fetchall()
    users = conn.execute("SELECT id,name,email,role FROM users ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", questions=questions, users=users)

@app.route("/admin/add", methods=["POST"])
@login_required
@admin_required
def add_question():
    data = [request.form[k] for k in
            ["subject","topic","question","option_a","option_b","option_c","option_d","answer","difficulty"]]
    conn=get_db()
    conn.execute("""INSERT INTO questions
        (subject,topic,question,option_a,option_b,option_c,option_d,answer,difficulty)
        VALUES (?,?,?,?,?,?,?,?,?)""", data)
    conn.commit(); conn.close()
    flash("Question added successfully.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:qid>")
@login_required
@admin_required
def delete_question(qid):
    conn=get_db(); conn.execute("DELETE FROM questions WHERE id=?", (qid,))
    conn.commit(); conn.close()
    flash("Question deleted.", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
