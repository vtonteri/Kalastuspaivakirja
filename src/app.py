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
    """
    Method that returns index page when Flask server is started and is called. 
    """
    sql = text("SELECT * FROM users ORDER BY username DESC")
    result = db.session.execute(sql)
    users = result.fetchall()
    return render_template("index.html", users = users)

@app.route("/login", methods=["POST"])
def login():
    """
    Method is called from index.html, when user tries to log in to application.
    Args: username and password
    
    Method returns either error message (if username or password is incorrect) or
    main_view.html page. Method sets session["username"], session["csrf_token"] and session["user_id"] parameters
    """
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
    """
    Method is called from index.html when user wants to create a new user.
    Args: new_username and new_password

    Method checks if username already exists and if not creates new user.

    Method returns index.html and message if creation was successful and error message otherwise.
    """

    new_username = request.form["new_username"]
    new_password = request.form["new_password"]

    if new_username and new_password:
        sql_username_exist = text("SELECT EXISTS(SELECT user FROM users WHERE username=:username)")
        result_exist = db.session.execute(sql_username_exist, {"username":new_username})
        result_username_exist = result_exist.fetchone()[0]
        if result_username_exist == False:
            try:

                if len(new_password) < 8:
                    raise Exception
                hash_value = generate_password_hash(new_password)
                sql = text("INSERT INTO users (username, password, created_at) VALUES (:username, :password, NOW())")
                db.session.execute(sql, {"username":new_username, "password":hash_value})
                db.session.commit()
                return render_template("/index.html", create_new_user_message = "New user created successfully! Now you can login with username and password")
            except:
                db.session.rollback()
                return render_template("/index.html", create_new_user_error_message = "Username already in use or too short password (password should contain at least 8 characters)! Choose another one!")
            
        elif result_username_exist == True:
            return render_template("/index.html", create_new_user_error_message = "Username already in use, please choose another one!")

    elif not new_username or not new_password:
        return render_template("/index.html", create_new_user_error_message = "Enter new username and password!")

@app.route("/create_fishing_season", methods=["POST"])
def create_fishing_season():

    """
    Method is called from main_view.html. It creates a new fishing season.

    Args: fishing_season. 

    Method checks if csfr-token is correct, the input is correct and the user has not already added season. 
    If token and input are correct and the user has not already added season, method injects a new season into
    database and returns main_view.html with all users fishing_seasons.
    If input is incorrect or season has already added, error message is shown.
    """

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

    """
    Method is called from main_view. 
    Args: selected season from selection at main_view.html and fetches all fishing days assosiated to that season.

    Method returns edit_season.html with information about all days associated to the selected season. 
    """
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    try:
        session["season_year"] = request.form["edit_season_year"]
        login_username = session["username"]

        sql_season = text("SELECT season_id FROM seasons WHERE user_id = :user_id AND season = :season")
        season_result = db.session.execute(sql_season, {"user_id": session["user_id"], "season": session["season_year"]})
        season_id = season_result.fetchone()[0]

        session["season_id"] = season_id

        sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
        day_result = day_result_rows.fetchall()
        return render_template("edit_season.html", selected_season = session["season_year"], login_username = login_username, day_result = day_result)
    except:
        return render_template("main_view.html")

@app.route("/create_fishing_day", methods = ["POST"])
def create_fishing_day():
    """
    Method is called from edit_season.html.
    Args: season, month and day for the fishing day to be created.

    Method checks csrf_token, and input. If they are correct then method checks if day already exist. If it does, it returns error message.
    If day is not created, it returns edit_season.html with success message.
    """
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    selected_season = request.form["selected_season"]
    month_to_database = request.form["month"]
    day_to_database = request.form["day"]
    date_to_database = f"{selected_season}-{month_to_database}-{day_to_database}"

    try:
       
        if int(month_to_database) > 12 or int(month_to_database) < 1:
            raise Exception
        if int(day_to_database) < 1 or int(day_to_database) > 31:
            raise Exception

        sql_exists = text("SELECT EXISTS(SELECT date_created FROM fishing_days WHERE season_id = :season_id AND date_created = :date_created)")
        result_if_exists_2 = db.session.execute(sql_exists, {"season_id": session["season_id"], "date_created": date_to_database})
        result_to_compare_if_exists_2 = result_if_exists_2.fetchone()[0]

        sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
        day_result = day_result_rows.fetchall()
        
        if result_to_compare_if_exists_2 == False:
            try:
                sql = text("INSERT INTO fishing_days (season_id, date_created) VALUES (:season_id, :date_created)")
                db.session.execute(sql, {"season_id": session["season_id"], "date_created": date_to_database})
                db.session.commit()
                
                sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
                day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
                day_result = day_result_rows.fetchall()

                return render_template("edit_season.html", create_new_day_message = "Fishing day created succesfully!", selected_season = selected_season, day_result = day_result)
            except:
                return render_template("edit_season.html", create_new_day_error_message = "Something went wrong, try again!", selected_season = selected_season, day_result = day_result)
        
        elif result_to_compare_if_exists_2 == True:
            return render_template("edit_season.html", create_new_day_error_message = "Day already exists! Create new or edit existing!", selected_season = selected_season, day_result = day_result)

    except:
        print("tässä ollaan2")
        sql_days = text("SELECT date_created FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
        day_result = day_result_rows.fetchall()
        return render_template("edit_season.html", create_new_day_error_message = "Something went wrong, try again, perhaps with correct values (month 1 - 12 and days 1 - 31)!", selected_season = selected_season, day_result = day_result)

    return render_template("edit_season.html", create_new_day_message = "Fishing day created succesfully!", day_result = day_result, selected_season = selected_season)

@app.route("/main_view", methods =["POST"])
def main_view():
    """
    Method is used to move between views. This method is called from edit_day.html and explore.html
    It returns main_view.html with users fishing seasons.
    """
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
    """
    Method is used to move between views. This method is called from edit_day.html
    It returns edit_season_view.html with users fishing days.
    """
    sql = text("SELECT season FROM seasons WHERE season_id=:season_id")
    result = db.session.execute(sql, {"season_id": session["season_id"]})
    season = result.fetchone()[0]

    sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
    day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
    day_result = day_result_rows.fetchall()

    return render_template("/edit_season.html", selected_season = season, day_result = day_result)
    
@app.route("/edit_day_view", methods =["POST"])
def edit_day():
    """
    Method is from edit_season.html
    Args: method takes selected fishing day as input and forwards it to edit_day.html
    It returns edit_day.html with users fishing days.
    """
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    selected_day_id = request.form["day_id"]
    session["day_id"] = selected_day_id

    sql = text("SELECT date_created FROM fishing_days WHERE day_id =:day_id")
    result = db.session.execute(sql, {"day_id": session["day_id"]})
    selected_day = result.fetchone()[0]
    session["date"] = selected_day

    return render_template("/edit_day.html", selected_day = selected_day, selected_day_id = selected_day_id)

@app.route("/add_fish", methods = ["POST"])
def add_fish():
    """
    Method is called from edit_day.html.
    Args: method takes fish type, length and weight as input.
    Method checks csrf-token and inputs. If they are correct, in inserts new fish to database associated to a selected day.
    Method returns error message if database insertion was not succesful. If it was, then success message is returned.
    """

    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)

    fish_type = request.form["fish_type"]
    fish_weight = request.form["fish_weight"]
    fish_length = request.form["fish_length"]

    if fish_type and fish_weight and fish_weight:
        try:
            fish_length = float(fish_length)
            fish_weight = float(fish_weight)
            if fish_length <= 0 or fish_weight <= 0:
                return render_template("/edit_day.html", fish_added_error_message = "Catch was not added, try again, maybe with correct values!")
            sql = text("INSERT INTO catched_fish (fishing_day_id, fish_type, fish_length, fish_weight) VALUES (:fishing_day_id, :fish_type, :fish_length, :fish_weight)")
            db.session.execute(sql, {"fishing_day_id":session["day_id"], "fish_type":fish_type, "fish_length":fish_length, "fish_weight":fish_weight})
            db.session.commit()
            return render_template("/edit_day.html", fish_added_message = "Catch added succesfully!")
        except:
            return render_template("/edit_day.html", fish_added_error_message = "Catch was not added, try again, maybe with correct values!")
    else:
        return render_template("/edit_day.html", fish_added_error_message = "Fill all required fields with correct values!")

@app.route("/add_weather", methods = ["POST"])
def add_weather():
    """
    Method is called from edit_day.html.
    Args: method takes temperature, visibility, wind speed, wind direction, and air pressure as input.
    Method checks csrf-token, inputs and if weather has already added to day. If they are correct and no weather already exist, 
    it inserts new weather to database associated to a selected day.
    Method returns error message if database insertion was not succesful. If it was, then success message is returned.
    """
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    temperature = request.form["temperature"]
    lightning = request.form["visibility"]
    wind_speed = request.form["wind_speed"]
    wind_direction = request.form["wind_direction"]
    wind_type = f"{wind_direction} {wind_speed}"
    air_pressure = request.form["air_pressure"]

    sql_weather_exist = text("SELECT EXISTS(SELECT temperature FROM weather WHERE fishing_day_id=:fishing_day_id)")
    result = db.session.execute(sql_weather_exist, {"fishing_day_id":session["day_id"]})
    result_if_weather_exist = result.fetchone()[0]

    if result_if_weather_exist == False and temperature and lightning and wind_speed and wind_direction and wind_type and air_pressure:
        try:
            sql = text("INSERT INTO weather (fishing_day_id, temperature, wind_type, pressure, lightning) VALUES (:fishing_day_id, :temperature, :wind_type, :pressure, :lightning)")
            db.session.execute(sql, {"fishing_day_id":session["day_id"], "temperature":temperature, "wind_type":wind_type, "pressure": air_pressure, "lightning":lightning})
            db.session.commit()
            return render_template("/edit_day.html", weather_added_message = "Weather added succesfully!")
        except:
            return render_template("/edit_day.html", weather_added_error_message = "Weather was not added, try again!")
        
    elif result_if_weather_exist == True:
        return render_template("/edit_day.html", weather_added_error_message = "Weather was already added!")
    else:
        return render_template("/edit_day.html", weather_added_error_message = "Fill all required fields with correct data!")

@app.route("/explore_fish", methods = ["POST"])
def explore_fish():
    """
    Method fetches information from the database and returns total number of fish catched, all fish, biggest fish, average fish weights and weather during the selected day, 
    """
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    selected_day_id = request.form["day_id"]
    session["day_id"] = selected_day_id
    
    sql = text("SELECT * FROM catched_fish WHERE fishing_day_id=:fishing_day_id ORDER BY fish_type")
    result = db.session.execute(sql, {"fishing_day_id": session["day_id"]})
    all_fish = result.fetchall()

    sql = text("SELECT * FROM catched_fish cf WHERE cf.fishing_day_id=:fishing_day_id AND (cf.fish_type, cf.fish_weight) IN (SELECT fish_type, MAX(fish_weight) FROM catched_fish WHERE fishing_day_id=:fishing_day_id GROUP BY fish_type);")
    result = db.session.execute(sql, {"fishing_day_id":session["day_id"]})
    biggest_fish = result.fetchall()

    sql = text("SELECT fish_type, AVG(fish_weight) AS avg_weight FROM catched_fish WHERE fishing_day_id=:fishing_day_id GROUP BY fish_type;")
    result = db.session.execute(sql, {"fishing_day_id":session["day_id"]})
    average_fish = result.fetchall()

    sql = text("SELECT fish_type, COUNT(*) AS num_fish FROM catched_fish WHERE fishing_day_id=:fishing_day_id GROUP BY fish_type;")
    result = db.session.execute(sql, {"fishing_day_id":session["day_id"]})
    how_many_fish = result.fetchall()

    sql = text("SELECT COUNT(*) AS total_fish FROM catched_fish WHERE fishing_day_id=:fishing_day_id;")
    result = db.session.execute(sql, {"fishing_day_id":session["day_id"]})
    total_fish = result.fetchone()[0]

    sql = text("SELECT * FROM weather WHERE fishing_day_id=:fishing_day_id;")
    result = db.session.execute(sql, {"fishing_day_id":session["day_id"]})
    weather = result.fetchall()

    return render_template("/explore.html", all_fish = all_fish, biggest_fish = biggest_fish, average_fish = average_fish, how_many_fish = how_many_fish, total_fish = total_fish, weather = weather)

@app.route("/delete_day", methods=["POST"])
def delete_day():

    """
    Method deletes selected fishing day and all associated fish and weather data.
    Args: selected day
    Method returns edit_season.html with all fishing days after deletion.
    """
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    selected_day_id = request.form["day_id"]

    try:
        sql_delete = text("DELETE FROM fishing_days WHERE day_id=:day_id")
        db.session.execute(sql_delete, {"day_id":selected_day_id})
        db.session.commit()
    except:
        sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
        day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
        day_result = day_result_rows.fetchall()
        return render_template("/edit_season.html", day_result = day_result, delete_day_error_message = "Day was deleted, try again!")

    sql_days = text("SELECT * FROM fishing_days WHERE season_id = :season_id ORDER BY date_created")
    day_result_rows = db.session.execute(sql_days, {"season_id":session["season_id"]})
    day_result = day_result_rows.fetchall()

    return render_template("/edit_season.html", day_result = day_result, delete_day_message = "Day and its associated fish and weather deleted succesfully!")

@app.route("/logout", methods=["GET"])
def logout():
    """
    Method is called from main_view.html, edit_season.html, edit_day.html and explore.html.
    Method deletes session-data and returns blank index.html.
    """
    try: 
        session["username"]
    except:
        pass
    try:
        del session["day_id"]
    except:
        pass
    try: 
        del session["user_id"]
    except:
        pass
    try:
        del session["csrf_token"]
    except:
        pass
    try: 
        del session["date"]
    except:
        pass
    try: 
        del session["season_id"]
    except:
        pass
    try: 
        del session["season_year"]
    except:
        pass
    return redirect("/")
