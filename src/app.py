from flask import Flask
from flask import render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from services import Check_Password_Own_Method
from services import Check_Username_Own_Method


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)
app.secret_key = getenv("SECRET_KEY")

@app.route("/")
def index():
    sql = text("SELECT * FROM users ORDER BY username DESC")
    result = db.session.execute(sql)
    users = result.fetchall()
    return render_template("index.html", users = users)

@app.route("/login", methods=["POST"])
def login():
    login_username = request.form["login_username"]
    login_password = request.form["login_password"]
    # TODO: check username and password

    session["username"] = login_username
    return redirect("/")

@app.route("/create_new_user", methods=["POST"])
def create_new_user():
    new_username = request.form["new_username"]
    new_password = request.form["new_password"]
    # TODO: check username and password
    if Check_Username_Own_Method.check_username(new_username) and Check_Password_Own_Method.check_password(new_password):
        pass



    hash_value = generate_password_hash(new_password)
    sql = text("INSERT INTO users (username, password) VALUES (:username, :password)")
    db.session.execute(sql, {"username":new_username, "password":hash_value})
    db.session.commit()
    return render_template("create_new_user.html")
