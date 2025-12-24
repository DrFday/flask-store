from flask import Flask, render_template, request, redirect, session, send_from_directory
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS_FILE = os.path.join(BASE_DIR, "users.json")
HISTORY_FILE = os.path.join(BASE_DIR, "purchase_history.json")

app = Flask(__name__)
app.secret_key = "secretkey123"

BOOKS = [
    {"id": 1, "title": "Black Clover v01", "price": 15, "cover": "BCv01.jpg", "file": "BCv01.pdf"},
    {"id": 2, "title": "Black Lagoon v08", "price": 15, "cover": "BLv08.jpg", "file": "BLv08.pdf"},
    {"id": 5, "title": "One-Punch Man v01", "price": 15, "cover": "OPMv01.jpg", "file": "OPMv01.pdf"},
    {"id": 7, "title": "Re：ZERO Vol. 07", "price": 15, "cover": "RZv07.jpg", "file": "RZv07.epub"},
    {"id": 8, "title": "Y0_MANGA", "price": 1, "cover": "Y0_MANGA.jpg", "file": "Y0_MANGA.pdf"},
    {"id": 3, "title": "Crysis Comic 01", "price": 1, "cover": "Crysis 01.jpg", "file": "Crysis 01.cbr"},
    {"id": 4, "title": "DXU THE DAWNING DARKNESS", "price": 1, "cover": "DXU_THE_DAWNING_DARKNESS.jpg", "file": "DXU_THE_DAWNING_DARKNESS.pdf"},
    {"id": 6, "title": "Ratchet & Clank 01", "price": 1, "cover": "rac.jpg", "file": "Ratchet & Clank 01.Cbz"},
]

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

with open(HISTORY_FILE, "r") as f:
    history = json.load(f)

@app.route("/")
def index():
    owned_ids = []
    cart_ids = []

    if "user" in session:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)

        for record in history:
            if record["username"] == session["user"]:
                owned_ids = record["books"]
                break

    if "cart" in session:
        cart_ids = [book["id"] for book in session["cart"]]

    return render_template(
        "index.html",
        books=BOOKS,
        owned_ids=owned_ids,
        cart_ids=cart_ids
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open(USERS_FILE, "r") as f:
            users = json.load(f)

        for u in users:
            if u["username"] == username:
                return "User already exists"

        users.append({
            "username": username,
            "password": password
        })

        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open(USERS_FILE, "r") as f:
            users = json.load(f)

        for u in users:
            if u["username"] == username and u["password"] == password:
                session["user"] = username
                session["cart"] = []
                return redirect("/")

        return "Invalid credentials"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/add/<int:book_id>")
def add_to_cart(book_id):
    if "user" not in session:
        return redirect("/login")

    if "cart" not in session:
        session["cart"] = []

    cart_ids = [book["id"] for book in session["cart"]]
    if book_id in cart_ids:
        return redirect("/")

    for book in BOOKS:
        if book["id"] == book_id:
            session["cart"].append(book)
            session.modified = True  
            break

    return redirect("/")

@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(book["price"] for book in cart)
    return render_template("cart.html", cart=cart, total=total)

@app.route("/buy")
def buy():
    if "user" not in session:
        return redirect("/login")

    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    username = session["user"]

    cart_ids = [book["id"] for book in session.get("cart", [])]

    user_record = None
    for record in history:
        if record["username"] == username:
            user_record = record
            break

    if user_record:
        owned_ids = user_record["books"]
        new_ids = [bid for bid in cart_ids if bid not in owned_ids]
        user_record["books"].extend(new_ids)
    else:
        new_ids = cart_ids
        history.append({
            "username": username,
            "books": new_ids
        })

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

    session["cart"] = []
    session.modified = True

    return redirect("/history")

@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    user_books = []

    for record in history:
        if record["username"] == session["user"]:
            for book_id in record["books"]:
                for book in BOOKS:
                    if book["id"] == book_id:
                        user_books.append(book)

    return render_template("history.html", history=user_books)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("static/downloads", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
