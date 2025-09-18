from flask import Flask, render_template, request, redirect, url_for, flash, session
import json, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"  # session জন্য

# ------------------ JSON Helpers ------------------
def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ------------------ Home Page ------------------
@app.route("/")
def home():
    return render_template("index.html")

# ------------------ Register ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("register"))

        users = load_json("users.json")
        if any(user["username"] == username for user in users):
            flash("Username already exists!", "error")
            return redirect(url_for("register"))

        users.append({
            "fullname": fullname,
            "username": username,
            "email": email,
            "phone": phone,
            "password": generate_password_hash(password)  # hashed password
        })
        save_json("users.json", users)
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ------------------ Login ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_json("users.json")
        user = next((u for u in users if u["username"] == username), None)

        if user and check_password_hash(user["password"], password):
            session["username"] = username  # save session
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# ------------------ Dashboard ------------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))

    username = session["username"]
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username), None)
    fullname = user["fullname"] if user else username
    centers = load_json("centers.json")
    return render_template("dashboard.html", username=username, fullname=fullname, centers=centers)

# ------------------ Logout ------------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# ------------------ Book a Center ------------------
@app.route("/book/<center_id>", methods=["GET", "POST"])
def book(center_id):
    if "username" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))

    username = session["username"]
    centers = load_json("centers.json")
    center = next((c for c in centers if c["id"] == center_id), None)
    bookings = load_json("bookings.json")

    if request.method == "POST":
        date = request.form["date"]
        time = request.form["time"]
        if any(b["center_id"]==center_id and b["date"]==date and b["time"]==time for b in bookings):
            flash("This slot is already booked!", "error")
            return redirect(url_for("book", center_id=center_id))

        bookings.append({
            "username": username,
            "center_id": center_id,
            "center_name": center["name"],
            "date": date,
            "time": time
        })
        save_json("bookings.json", bookings)
        flash("Booking successful!", "success")
        return redirect(url_for("dashboard"))

    return render_template("book.html", center=center, username=username)

# ------------------ View Bookings ------------------
@app.route("/view_bookings")
def view_bookings():
    if "username" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))

    username = session["username"]
    bookings = load_json("bookings.json")
    user_bookings = [b for b in bookings if b["username"] == username]
    return render_template("view_bookings.html", bookings=user_bookings, username=username)

# ------------------ Cancel Booking ------------------
@app.route("/cancel/<center_id>/<date>/<time>")
def cancel_booking(center_id, date, time):
    if "username" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))

    username = session["username"]
    bookings = load_json("bookings.json")
    bookings = [b for b in bookings if not (b["username"]==username and b["center_id"]==center_id and b["date"]==date and b["time"]==time)]
    save_json("bookings.json", bookings)
    flash("Booking canceled!", "info")
    return redirect(url_for("view_bookings"))

# ------------------ Initialize centers.json ------------------
if __name__ == "__main__":
    if not os.path.exists("centers.json"):
        centers = [
            {"id":"c1","name":"Community Hall A","location":"Dhaka","capacity":50,"cost":500},
            {"id":"c2","name":"Community Hall B","location":"Chittagong","capacity":100,"cost":1000},
            {"id":"c3","name":"Community Hall C","location":"Sylhet","capacity":30,"cost":300}
        ]
        save_json("centers.json", centers)
    app.run(debug=True)
