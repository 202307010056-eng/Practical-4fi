from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3

app = Flask(__name__)
app.secret_key = "final_year_secret_key"
DB = "attendance.db"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        status TEXT
    )""")

    # default users
    cur.execute("SELECT * FROM users")
    if not cur.fetchall():
        cur.execute("INSERT INTO users VALUES(NULL,'admin','admin123','admin')")
        cur.execute("INSERT INTO users VALUES(NULL,'teacher','teacher123','teacher')")
        cur.execute("INSERT INTO users VALUES(NULL,'student','student123','student')")

    conn.commit()
    conn.close()

init_db()

# ---------------- CSS ----------------
css = """
<style>
body{
    font-family:Segoe UI;
    background:linear-gradient(to right,#141E30,#243B55);
    color:white;
    margin:0;
}
.container{
    width:420px;
    margin:90px auto;
    background:rgba(0,0,0,0.65);
    padding:30px;
    border-radius:14px;
    box-shadow:0 0 25px black;
    text-align:center;
}
h2,h3{
    margin-bottom:20px;
}
input,button{
    width:100%;
    padding:12px;
    margin-top:12px;
    border:none;
    border-radius:8px;
    font-size:15px;
}
button{
    background:#00c6ff;
    font-weight:bold;
    cursor:pointer;
}
button:hover{
    background:#00a6d6;
}
a{
    color:#00c6ff;
    text-decoration:none;
    font-weight:500;
}
a:hover{
    text-decoration:underline;
}
table{
    width:100%;
    border-collapse:collapse;
    margin-top:15px;
}
th,td{
    padding:10px;
    border:1px solid #ccc;
}
p.small{
    font-size:13px;
    opacity:0.7;
}
</style>
"""

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]

        conn=sqlite3.connect(DB)
        cur=conn.cursor()
        cur.execute("SELECT role FROM users WHERE username=? AND password=?", (u,p))
        user=cur.fetchone()
        conn.close()

        if user:
            session["role"]=user[0]
            return redirect(url_for("dashboard"))
        else:
            error="Invalid username or password"

    return render_template_string(css+"""
    <div class="container">
    <h2>Smart Attendance Management System</h2>
    <form method="post">
    <input name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button>Login</button>
    </form>
    <p style="color:#ff6b6b;">{{error}}</p>
    <p class="small">
    Authorized users only. Please login using your credentials.
    </p>
    </div>
    """,error=error)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    role=session.get("role")

    if role=="admin":
        return render_template_string(css+"""
        <div class="container">
        <h3>Admin Dashboard</h3>
        <a href="/add_student">➕ Add Student</a><br><br>
        <a href="/remove_student">🗑 Remove Student</a><br><br>
        <a href="/view_attendance">📊 View Attendance</a><br><br>
        <a href="/logout">🚪 Logout</a>
        </div>
        """)

    if role=="teacher":
        return render_template_string(css+"""
        <div class="container">
        <h3>Teacher Dashboard</h3>
        <a href="/mark_attendance">📝 Mark Attendance</a><br><br>
        <a href="/view_attendance">📊 View Attendance</a><br><br>
        <a href="/logout">🚪 Logout</a>
        </div>
        """)

    if role=="student":
        return render_template_string(css+"""
        <div class="container">
        <h3>Student Dashboard</h3>
        <a href="/view_attendance">📊 View Attendance</a><br><br>
        <a href="/logout">🚪 Logout</a>
        </div>
        """)

    return redirect(url_for("login"))

# ---------------- ADD STUDENT ----------------
@app.route("/add_student",methods=["GET","POST"])
def add_student():
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    if request.method=="POST":
        name=request.form["name"]
        conn=sqlite3.connect(DB)
        cur=conn.cursor()
        cur.execute("INSERT INTO students VALUES(NULL,?)",(name,))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    return render_template_string(css+"""
    <div class="container">
    <h3>Add Student</h3>
    <form method="post">
    <input name="name" placeholder="Student Name" required>
    <button>Add Student</button>
    </form>
    <br><a href="/dashboard">⬅ Back</a>
    </div>
    """)

# ---------------- REMOVE STUDENT ----------------
@app.route("/remove_student")
def remove_student():
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    students=cur.execute("SELECT * FROM students").fetchall()
    conn.close()

    html=css+"""<div class="container">
    <h3>Remove Student</h3>
    <table>
    <tr><th>ID</th><th>Name</th><th>Action</th></tr>"""

    for s in students:
        html+=f"""
        <tr>
            <td>{s[0]}</td>
            <td>{s[1]}</td>
            <td><a href="/delete_student/{s[0]}">Delete</a></td>
        </tr>
        """

    html+="</table><br><a href='/dashboard'>⬅ Back</a></div>"
    return render_template_string(html)

# ---------------- DELETE STUDENT ----------------
@app.route("/delete_student/<int:sid>")
def delete_student(sid):
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    conn=sqlite3.connect(DB)
    cur=conn.cursor()

    cur.execute("DELETE FROM attendance WHERE student_id=?", (sid,))
    cur.execute("DELETE FROM students WHERE id=?", (sid,))

    conn.commit()
    conn.close()

    return redirect(url_for("remove_student"))

# ---------------- MARK ATTENDANCE ----------------
@app.route("/mark_attendance",methods=["GET","POST"])
def mark_attendance():
    if session.get("role")!="teacher":
        return redirect(url_for("login"))

    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    students=cur.execute("SELECT * FROM students").fetchall()

    if request.method=="POST":
        for s in students:
            status=request.form.get(str(s[0]))
            cur.execute("INSERT INTO attendance VALUES(NULL,?,?)",(s[0],status))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    html=css+"""<div class="container"><h3>Mark Attendance</h3><form method="post">"""
    for s in students:
        html+=f"""
        <p style="text-align:left;">{s[1]} :
        <input type="radio" name="{s[0]}" value="Present" required> Present
        <input type="radio" name="{s[0]}" value="Absent"> Absent</p>
        """
    html+="""<button>Submit Attendance</button></form><br><a href="/dashboard">⬅ Back</a></div>"""
    return render_template_string(html)

# ---------------- VIEW ATTENDANCE ----------------
@app.route("/view_attendance")
def view_attendance():
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    data=cur.execute("""
    SELECT students.name, attendance.status
    FROM attendance
    JOIN students ON students.id=attendance.student_id
    """).fetchall()

    html=css+"""<div class="container">
    <h3>Attendance Report</h3>
    <table><tr><th>Name</th><th>Status</th></tr>"""
    for d in data:
        html+=f"<tr><td>{d[0]}</td><td>{d[1]}</td></tr>"
    html+="</table><br><a href='/dashboard'>⬅ Back</a></div>"
    return render_template_string(html)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- RUN ----------------
if __name__=="__main__":
    app.run(debug=True)
