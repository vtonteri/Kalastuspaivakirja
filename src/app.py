from flask import Flask
from flask import render_template, request, redirect, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
import secrets



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
            session["csrf_token"] = secrets.token_hex(16)
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

    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
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

        sql = text("SELECT user_id FROM users WHERE username =:login_username")
        result = db.session.execute(sql, {"login_username": login_username})
        user_id = result.fetchone()[0]
        print("virhe 1")
        sql_season = text("SELECT season_id FROM seasons WHERE user_id = :user_id AND season = :season")
        season_result = db.session.execute(sql_season, {"user_id": user_id, "season": selected_season})
        season_id = season_result.fetchone()[0]
        print("virhe 2")
        sql_days = text("SELECT date_created FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":season_id})
        day_result = day_result_rows.fetchall()
        print("virhe 3")
        return render_template("edit_season.html", selected_season = selected_season, login_username = login_username, day_result = day_result)
    except:
        print("virhe 4")
        return render_template("main_view.html")
    
@app.route("/send_data_edit_day", methods=["POST"])
def send_data_edit_day():
    try:
        selected_season = request.form["edit_season_year"]
        login_username = session["username"]

        sql = text("SELECT user_id FROM users WHERE username =:login_username")
        result = db.session.execute(sql, {"login_username": login_username})
        user_id = result.fetchone()[0]
        print("virhe 1 day")
        sql_season = text("SELECT season_id FROM seasons WHERE user_id = :user_id AND season = :season")
        season_result = db.session.execute(sql_season, {"user_id": user_id, "season": selected_season})
        season_id = season_result.fetchone()[0]
        print("virhe 2 day")
        sql_days = text("SELECT date_created FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":season_id})
        day_result = day_result_rows.fetchall()
        print("virhe 3 day")
        return render_template("edit_season.html", selected_season = selected_season, login_username = login_username, day_result = day_result)
    except:
        print("virhe 4 day")
        return render_template("main_view.html")

@app.route("/create_fishing_day", methods = ["POST"])
def create_fishing_day():
    selected_season = request.form["selected_season"]
    login_username = session["username"]
    month_to_database = request.form["month"]
    day_to_database = request.form["day"]
    date_to_database = f"{selected_season}-{month_to_database}-{day_to_database}"
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    try:
        sql = text("SELECT user_id FROM users WHERE username = :username")
        result = db.session.execute(sql, {"username":login_username})
        user_id = result.fetchone()[0]

        sql = text("SELECT season_id FROM seasons WHERE user_id = :user_id AND season = :season")
        result = db.session.execute(sql, {"user_id":user_id, "season":selected_season})
        season_id = result.fetchone()[0]

        sql_exists = text("SELECT EXISTS(SELECT date_created FROM fishing_days WHERE season_id = :season_id AND date_created = :date_created)")
        result_if_exists_2 = db.session.execute(sql_exists, {"season_id": season_id, "date_created": date_to_database})
        result_to_compare_if_exists_2 = result_if_exists_2.fetchone()[0]

        sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":season_id})
        day_result = day_result_rows.fetchall()
        

        if result_to_compare_if_exists_2 == False:
            try:
                sql = text("INSERT INTO fishing_days (season_id, date_created) VALUES (:season_id, :date_created)")
                result = db.session.execute(sql, {"season_id": season_id, "date_created": date_to_database})
                db.session.commit()
                
                sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
                day_result_rows = db.session.execute(sql_days, {"season_id":season_id})
                day_result = day_result_rows.fetchall()

                return render_template("edit_season.html", create_new_day_message = "Fishing day created succesfully!", selected_season = selected_season, day_result = day_result)
            except:
                return render_template("edit_season.html", create_new_day_error_message = "Something went wrong 2, try again!", selected_season = selected_season, day_result = day_result)
        
        elif result_to_compare_if_exists_2 == True:
            return render_template("edit_season.html", create_new_day_error_message = "Day already exists! Create new or edit existing!", selected_season = selected_season, day_result = day_result)

    except:
        sql_days = text("SELECT date_created FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":season_id})
        day_result = day_result_rows.fetchall()
        return render_template("edit_season.html", create_new_day_error_message = "Something went wrong 1, try again!", selected_season = selected_season, day_result = day_result)

    #sql = text("SELECT * FROM fishing_days WHERE season_id = :season_id AND date_created = :date_created")
    #result = db.session.execute(sql, {"season_id": season_id, "date_created": date_to_database})
    #fishing_days = result.fetchall()

    return render_template("edit_season.html", create_new_day_message = "Fishing day created succesfully!", day_result = day_result, selected_season = selected_season)

@app.route("/main_view", methods =["POST"])
def main_view():
    login_username = session["username"]
    sql = text("SELECT user_id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username":login_username})
    user = result.fetchone()

    try:
        sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
        result = db.session.execute(sql, {"user_id": user[0]})
        seasons = result.fetchall()
        return render_template("/main_view.html", user = user, login_username = login_username, seasons = seasons)            
    except:
        return render_template("/main_view.html", user = user, login_username = login_username)

@app.route("/logout", methods=["GET"])
def logout():
    del session["username"]
    return redirect("/")
