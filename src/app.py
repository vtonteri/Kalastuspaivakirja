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
            session["user_id"] = user_id
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
        sql_username_exist = text("SELECT EXISTS(SELECT user FROM users WHERE username=:username)")
        result_exist = db.session.execute(sql_username_exist, {"username":new_username})
        result_username_exist = result_exist.fetchone()[0]
        if result_username_exist == False:
            try:
                hash_value = generate_password_hash(new_password)
                sql = text("INSERT INTO users (username, password, created_at) VALUES (:username, :password, NOW())")
                db.session.execute(sql, {"username":new_username, "password":hash_value})
                db.session.commit()
                return render_template("/index.html", create_new_user_message = "New user created successfully! Now you can login with username and password")
            except:
                db.session.rollback()
                return render_template("/index.html", create_new_user_error_message = "Username already in use! Choose another one!")
            
        elif result_username_exist == True:
            return render_template("/index.html", create_new_user_error_message = "Username already in use, please choose another one!")

    elif not new_username or not new_password:
        return render_template("/index.html", create_new_user_error_message = "Enter new username and password!")

@app.route("/create_fishing_season", methods=["POST"])
def create_fishing_season():

    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    try:
        fishing_season = int(request.form["season_year"])
    except ValueError:
        sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
        result = db.session.execute(sql, {"user_id": session["user_id"]})
        seasons = result.fetchall()
        return render_template("main_view.html", create_fishing_season_message_failure = "Enter valid season, eg. 2023", seasons = seasons)
    
    sql_exists = text("SELECT EXISTS(SELECT season FROM seasons WHERE user_id=:user_id AND season =:fishing_season)")
    result_if_exists = db.session.execute(sql_exists, {"user_id": session["user_id"], "fishing_season": fishing_season})
    result_to_compare_if_exists = result_if_exists.fetchone()[0]

    if result_to_compare_if_exists == False:
        try:
            sql = text("INSERT INTO seasons (user_id, season) VALUES (:user_id, :season)")
            db.session.execute(sql, {"user_id":session["user_id"], "season":fishing_season})
            db.session.commit()

            sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
            result = db.session.execute(sql, {"user_id": session["user_id"]})
            seasons = result.fetchall()

            return render_template("main_view.html", create_fishing_season_message_success = "Season added succesfully!", seasons = seasons)
        except:
            db.session.rollback()
            return render_template("main_view.html", create_fishing_season_message_failure = "Season was not added, try again!", seasons = seasons)
    
    elif result_to_compare_if_exists == True or not fishing_season:
        sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
        result = db.session.execute(sql, {"user_id": session["user_id"]})
        seasons = result.fetchall()
        return render_template("main_view.html", create_fishing_season_message_failure = "Season already exists!", seasons = seasons)

@app.route("/send_data_edit_season", methods = ["POST"])
def send_data_edit_season():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    try:
        session["season_year"] = request.form["edit_season_year"]
        login_username = session["username"]

        sql_season = text("SELECT season_id FROM seasons WHERE user_id = :user_id AND season = :season")
        season_result = db.session.execute(sql_season, {"user_id": session["user_id"], "season": session["season_year"]})
        season_id = season_result.fetchone()[0]

        session["season_id"] = season_id

        sql_days = text("SELECT date_created FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
        day_result = day_result_rows.fetchall()
        return render_template("edit_season.html", selected_season = session["season_year"], login_username = login_username, day_result = day_result)
    except:
        print("virhe 4")
        return render_template("main_view.html")
    
@app.route("/send_data_edit_day", methods=["POST"])
def send_data_edit_day():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    try:
        selected_season = request.form["edit_season_year"]
        login_username = session["username"]

        sql_days = text("SELECT date_created FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
        day_result = day_result_rows.fetchall()

        return render_template("edit_season.html", selected_season = selected_season, login_username = login_username, day_result = day_result)
    except:
        return render_template("main_view.html")

@app.route("/create_fishing_day", methods = ["POST"])
def create_fishing_day():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    selected_season = request.form["selected_season"]
    month_to_database = request.form["month"]
    day_to_database = request.form["day"]
    date_to_database = f"{selected_season}-{month_to_database}-{day_to_database}"
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    try:
        sql_exists = text("SELECT EXISTS(SELECT date_created FROM fishing_days WHERE season_id = :season_id AND date_created = :date_created)")
        result_if_exists_2 = db.session.execute(sql_exists, {"season_id": session["season_id"], "date_created": date_to_database})
        result_to_compare_if_exists_2 = result_if_exists_2.fetchone()[0]

        sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
        day_result = day_result_rows.fetchall()
        
        if result_to_compare_if_exists_2 == False:
            try:
                sql = text("INSERT INTO fishing_days (season_id, date_created) VALUES (:season_id, :date_created)")
                result = db.session.execute(sql, {"season_id": session["season_id"], "date_created": date_to_database})
                db.session.commit()
                
                sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
                day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
                day_result = day_result_rows.fetchall()

                return render_template("edit_season.html", create_new_day_message = "Fishing day created succesfully!", selected_season = selected_season, day_result = day_result)
            except:
                return render_template("edit_season.html", create_new_day_error_message = "Something went wrong 2, try again!", selected_season = selected_season, day_result = day_result)
        
        elif result_to_compare_if_exists_2 == True:
            return render_template("edit_season.html", create_new_day_error_message = "Day already exists! Create new or edit existing!", selected_season = selected_season, day_result = day_result)

    except:
        sql_days = text("SELECT date_created FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
        day_result = day_result_rows.fetchall()
        return render_template("edit_season.html", create_new_day_error_message = "Something went wrong 1, try again!", selected_season = selected_season, day_result = day_result)

    return render_template("edit_season.html", create_new_day_message = "Fishing day created succesfully!", day_result = day_result, selected_season = selected_season)

@app.route("/main_view", methods =["POST"])
def main_view():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    login_username = session["username"]
    sql = text("SELECT user FROM users WHERE user_id=:user_id")
    result = db.session.execute(sql, {"user_id":session["user_id"]})
    user = result.fetchone()

    try:
        sql = text("SELECT season FROM seasons WHERE user_id=:user_id ORDER BY season DESC")
        result = db.session.execute(sql, {"user_id": session["user_id"]})
        seasons = result.fetchall()
        return render_template("/main_view.html", user = user, login_username = login_username, seasons = seasons)            
    except:
        return render_template("/main_view.html", user = user, login_username = login_username)
    
@app.route("/edit_season_view", methods =["POST"])
def edit_season_view():
    sql = text("SELECT season FROM seasons WHERE season_id=:season_id")
    result = db.session.execute(sql, {"season_id": session["season_id"]})
    season = result.fetchone()[0]

    sql_days = text("SELECT date_created FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
    day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
    day_result = day_result_rows.fetchall()

    return render_template("/edit_season.html", selected_season = season, day_result = day_result)
    
@app.route("/edit_day_view", methods =["POST"])
def edit_day():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    selected_day = request.form["edit_fishing_day"]
    selected_day_id = request.form["day_id"]
    print(selected_day_id)
    sql = text("SELECT * FROM fishing_days WHERE season_id=:season_id")
    result = db.session.execute(sql, {"season_id":session["season_id"]})
    fishing_day = result.fetchall()[0]
    session["day_id"] = fishing_day[0]
    selected_day = fishing_day[2]

    return render_template("/edit_day.html", selected_day = selected_day, selected_day_id = selected_day_id)

@app.route("/add_fish", methods = ["POST"])
def add_fish():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    fish_type = request.form["fish_type"]
    fish_weight = request.form["fish_weight"]
    fish_length = request.form["fish_length"]

    if fish_type and fish_length and fish_weight:
        try:
            sql = text("INSERT INTO catched_fish (fishing_day_id, fish_type, fish_length, fish_weight) VALUES (:fishing_day_id, :fish_type, :fish_length, :fish_weight)")
            db.session.execute(sql, {"fishing_day_id":session["day_id"], "fish_type":fish_type, "fish_length":fish_length, "fish_weight":fish_weight})
            db.session.commit()
            return render_template("/edit_day.html", fish_added_message = "Catch added succesfully!")
        except:
            return render_template("/edit_day.html", fish_added_error_message = "Catch was not added, try again!")
    else:
        return render_template("/edit_day.html", fish_added_error_message = "Fill all required fields!")

@app.route("/add_weather", methods = ["POST"])
def add_weather():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    temperature = request.form["temperature"]
    lightning = request.form["visibility"]
    wind_speed = request.form["wind_speed"]
    wind_direction = request.form["wind_direction"]
    wind_type = f"{wind_direction} {wind_speed}"
    air_pressure = request.form["air_pressure"]
    print(f"{temperature} {lightning} {wind_type} {air_pressure}")

    sql_weather_exist = text("SELECT EXISTS(SELECT temperature FROM weather WHERE fishing_day_id=:fishing_day_id)")
    result = db.session.execute(sql_weather_exist, {"fishing_day_id":session["day_id"]})
    result_if_weather_exist = result.fetchone()[0]
    print(result_if_weather_exist)

    if result_if_weather_exist == False:
        print("1")
        try:
            print("2")
            sql = text("INSERT INTO weather (fishing_day_id, temperature, wind_type, pressure, lightning) VALUES (:fishing_day_id, :temperature, :wind_type, :pressure, :lightning)")
            print("3")
            db.session.execute(sql, {"fishing_day_id":session["day_id"], "temperature":temperature, "wind_type":wind_type, "pressure": air_pressure, "lightning":lightning})
            print("4")
            db.session.commit()
            return render_template("/edit_day.html", weather_added_message = "Weather added succesfully!")
        except:
            print("5")
            return render_template("/edit_day.html", weather_added_error_message = "Weather was not added, try again!")
        
    elif result_if_weather_exist == True:

        print("6")
        return render_template("/edit_day.html", weather_added_error_message = "Weather was already added!")    

@app.route("/logout", methods=["GET"])
def logout():
    del session["username"]
    return redirect("/")
