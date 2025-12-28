from flask import Flask, render_template, request, session, redirect, url_for
from backend.text_to_sql_langgraph_flow import (
    run_text_to_sql_preview,
    run_text_to_sql_execute
)

app = Flask(__name__)
app.secret_key = "your-secret-key-here"


# ------------------ USERS ------------------
USERS = {
    "ANU": {"password": "admin123", "role": "ADMIN", "empid": "101"},
    "PRIYA": {"password": "staff123", "role": "JUNIORDEV", "empid": "102"},
    "SANGU": {"password": "mgr123", "role": "MANAGER", "empid": "103"},
    "DIVYA": {"password": "staff123", "role": "INTERN", "empid": "104"},
    "SHERIN": {"password": "hrr123", "role": "HR", "empid": "105"},
    "AKSHARA": {"password": "staff123", "role": "SENIORDEV", "empid": "106"},
    "ATHARVA": {"password": "staff123", "role": "PROJECTMANAGER", "empid": "107"},
    "MAHA": {"password": "staff123", "role": "TEAMLEAD", "empid": "108"},
    "PRASHEETHA": {"password": "staff123", "role": "EMPLOYEE", "empid": "109"},
    "KAMALESH": {"password": "staff123", "role": "ASSOCIATEENGINEER", "empid": "110"},
    "MEENA": {"password": "staff123", "role": "ASSOCIATEENGINEER", "empid": "111"},
    "ABI": {"password": "staff123", "role": "ASSOCIATEENGINEER", "empid": "112"},
    "DHEERAJ": {"password": "staff123", "role": "ASSOCIATEENGINEER", "empid": "113"},
    "VIBHUDESH": {"password": "staff123", "role": "ASSOCIATEENGINEER", "empid": "114"},
    "RAHUL": {"password": "staff123", "role": "ASSOCIATEENGINEER", "empid": "115"},
}


# ------------------ LOGIN ------------------
@app.route("/")
def login_page():
    session.clear()
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").upper()
    password = request.form.get("password", "")
    role = request.form.get("role", "").upper()
    empid = request.form.get("empid", "")

    user = USERS.get(username)
    if user and user["password"] == password and user["role"] == role and user["empid"] == empid:
        session["username"] = username
        session["role"] = role
        session["empid"] = empid
        return redirect(url_for("home"))

    return render_template("login.html", error="Invalid credentials")


# ------------------ HOME ------------------
@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login_page"))
    return render_template(
        "home.html",
        username=session.get("username"),
        role=session.get("role")
    )


# ------------------ PREVIEW ------------------
@app.route("/query", methods=["POST"])
def query():
    user_input = request.form.get("query", "").strip()

    preview = run_text_to_sql_preview(
        user_input=user_input,
        role=session["role"],
        user_id=int(session["empid"])
    )

    return render_template(
        "result.html",
        sql=preview["sql"],
        explanation=preview["explanation"],
        show_confirm=True
    )


# ------------------ EXECUTE ------------------
@app.route("/execute", methods=["POST"])
def execute():
    sql = request.form.get("sql")

    result = run_text_to_sql_execute(
        sql=sql,
        role=session["role"],
        user_id=int(session["empid"])
    )

    return render_template(
        "result.html",
        sql=sql,
        columns=result["columns"],
        rows=result["rows"],
        show_confirm=False
    )


# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


if __name__ == "__main__":
    app.run(debug=True)

