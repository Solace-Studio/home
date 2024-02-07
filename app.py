import json
import base64
from flask import Flask, flash, redirect, render_template, request, session,g,jsonify,url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os
import random
from helpers import apology, login_required
import logging
import joblib




app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)






def get_db():
    """Open a new database connection if there is none yet for the current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect("users.db")
        g.sqlite_db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, hash TEXT NOT NULL)")
        g.sqlite_db.execute("CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL, game_link TEXT NOT NULL, picture TEXT NOT NULL, userid INTEGER NOT NULL)")
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Close the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route("/",methods=["GET"])
@login_required
def index():
    """Main Page"""
    return render_template("index.html")

@app.route("/submit",methods=["GET","POST"])
@login_required
def submit():
    """Submit a New Game with Name Descriptions Images in Base64 and Link to the Game"""

    if request.method == "POST":
        
        if not request.form.get("name"):
            return apology("Please Enter a Name")
        if not request.form.get("description"):
            return apology("Please Enter a Description")
        if not request.form.get("game_link"):
            return apology("Please Enter a Game Link")
        if not request.files.get("picture"):
            return apology("Please Enter a Picture")
        
        name = request.form.get("name")
        description = request.form.get("description")
        game_link = request.form.get("game_link")
        picture = request.files.get("picture")
        picture_string = base64.b64encode(picture.read()).decode("utf-8")
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO games (name,description,game_link,picture,userid) VALUES (?,?,?,?,?)",(name,description,game_link,picture_string,session["user_id"]))
        db.commit()
        return render_template("submit.html",success=True)
    else:
        return render_template("submit.html")




@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        rows = cursor.fetchall()

        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0][0]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Please Enter a Username")
        if not password or not confirmation or password != confirmation:
            return apology("Please correctly write both password fields")

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        duplicate = cursor.fetchone()

        if duplicate:
            return apology("Username already exists")

        passwordHash = generate_password_hash(password)

        cursor.execute("INSERT INTO users (username,hash) VALUES (?, ?)", (username, passwordHash))
        db.commit()

        return redirect("/login")

    else:
        return render_template("register.html")
