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

    sql = text("SELECT user_id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username":login_username})
    user = result.fetchone()
    
    if not user:
        db.session.rollback()
        return render_template("/index.html", login_error_message = "Incorrect username!")
    else:
        user_id = user[0]
        hash_value = user.password
        if check_password_hash(hash_value, login_password):
            session["username"] = login_username
            try:
                sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
                result = db.session.execute(sql, {"user_id": user_id})
                seasons = result.fetchall()
                return render_template("/main_view.html", user = user, login_username = login_username, seasons = seasons)            
            except:
                return render_template("/main_view.html", user = user, login_username = login_username)
        elif not check_password_hash(hash_value, login_password):
            db.session.rollback()
            return render_template("/index.html", login_error_message = "Incorrect password!")

@app.route("/create_new_user", methods=["POST"])
def create_new_user():
    new_username = request.form["new_username"]
    new_password = request.form["new_password"]
    if new_username and new_password:
        try:
            hash_value = generate_password_hash(new_password)
            sql = text("INSERT INTO users (username, password, created_at) VALUES (:username, :password, NOW())")
            db.session.execute(sql, {"username":new_username, "password":hash_value})
            db.session.commit()
            return render_template("create_new_user.html")
        except:
            db.session.rollback()
            return render_template("/index.html", create_new_user_error_message = "Username already in use! Choose another one!")
    elif not new_username or not new_password:
        return render_template("/index.html", create_new_user_error_message = "Enter new username and password!")

@app.route("/create_fishing_season", methods=["POST"])
def create_fishing_season():
    login_username = session["username"]
    sql = text("SELECT user_id FROM users WHERE username =:login_username")
    result = db.session.execute(sql, {"login_username": login_username})
    user_id = result.fetchone()[0]

    try:
        fishing_season = int(request.form["season_year"])
    except ValueError:
        sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
        result = db.session.execute(sql, {"user_id": user_id})
        seasons = result.fetchall()
        return render_template("main_view.html", create_fishing_season_message_failure = "Enter valid season, eg. 2023", seasons = seasons)
    
    sql_exists = text("SELECT EXISTS(SELECT season FROM seasons WHERE user_id=:user_id AND season =:fishing_season)")
    result_if_exists = db.session.execute(sql_exists, {"user_id": user_id, "fishing_season": fishing_season})
    result_to_compare_if_exists = result_if_exists.fetchone()[0]

    if result_to_compare_if_exists == False:
        try:
            sql = text("INSERT INTO seasons (user_id, season) VALUES (:user_id, :season)")
            db.session.execute(sql, {"user_id":user_id, "season":fishing_season})
            db.session.commit()

            sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
            result = db.session.execute(sql, {"user_id": user_id})
            seasons = result.fetchall()

            return render_template("main_view.html", create_fishing_season_message_success = "Season added succesfully!", seasons = seasons)
        except:
            db.session.rollback()
            return render_template("main_view.html", create_fishing_season_message_failure = "Season was not added, try again!", seasons = seasons)
    
    elif result_to_compare_if_exists == True or not fishing_season:
        sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
        result = db.session.execute(sql, {"user_id": user_id})
        seasons = result.fetchall()
        return render_template("main_view.html", create_fishing_season_message_failure = "Season already exists!", seasons = seasons)

@app.route("/send_data_edit_season", methods = ["POST"])
def send_data_edit_season():
    try:
        selected_season = request.form["edit_season_year"]
        login_username = session["username"]
        return render_template("edit_season.html", selected_season = selected_season, login_username = login_username)
    except:
        return render_template("main_view.html")

@app.route("/create_fishing_day", methods = ["POST"])
def create_fishing_day():
    #selected_season = request.form["selected_season"]
    return redirect("/")
    


@app.route("/logout", methods=["GET"])
def logout():
    del session["username"]
    return redirect("/")