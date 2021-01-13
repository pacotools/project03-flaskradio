import os
import requests
from flask import (
    Flask, flash, render_template, redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/", methods=["GET", "POST"])
def home():
    url = "https://freegeoip.app/json/"
    headers = {
        'accept': "application/json",
        'content-type': "application/json"
    }
    # get current country name
    response = requests.request("GET", url, headers=headers)
    session['country_name'] = response.json()["country_name"]
    # set first station id or set a default country and station
    existing_country = mongo.db.countries.find_one(
        {'name': session['country_name']})
    if existing_country:
        session['current_station'] = str(mongo.db.stations.find_one(
            {'country': session['country_name']})['_id'])
    else:
        session['country_name'] = 'Mexico'
        session['current_station'] = '5fd2b4e1cf81978844d648c2'
    session['user'] = ""
    return redirect(url_for('radio'))


@app.route('/radio_selector', methods=["GET", "POST"])
def radio_selector():
    session['country_name'] = request.form.get("country_name")
    f = request.form['selector']
    if f == 'station':
        session['current_station'] = request.form.get("station_id")
    else:
        session['current_station'] = str(mongo.db.stations.find_one(
            {'country': session['country_name']})['_id'])
    return redirect(url_for('radio'))


@app.route('/add_favorite', methods=["GET", "POST"])
def add_favorite():
    existing_station = str(mongo.db.favorites.find_one({
        'user': session['user'],
        'station_id': session['current_station']
    }))
    if existing_station == 'None':
        s = session["current_station"]
        station = mongo.db.stations.find_one({
            "_id": ObjectId(s)})
        station_info = {
            "country_name": session['country_name'],
            "station_id": session['current_station'],
            "user": session['user'],
            "url_resolved": station["url_resolved"],
            "station_name": station["name"],
            "homepage": station["homepage"],
            "favicon": station["favicon"],
            "tags": station["tags"],
        }
        mongo.db.favorites.insert_one(station_info)
    return redirect(url_for('radio'))


@app.route("/radio", methods=["GET", "POST"])
def radio():
    countries = list(mongo.db.countries.find().sort("name", 1))
    stations = list(mongo.db.stations.find(
        {'country': session['country_name']}))
    favorites = list(mongo.db.favorites.find(
        {'user': session['user'].lower()}))

    i = find_station(stations)

    station_info = {
        "country_name": stations[i]['country'],
        "station_id": stations[i]['_id'],
        "url_resolved": stations[i]['url_resolved'],
        "station_name": stations[i]['name'],
        "homepage": stations[i]['homepage'],
        "favicon": stations[i]['favicon'],
        "tags": stations[i]['tags'],
    }
    return render_template(
        "radio.html", station_info=station_info,
        countries=countries, stations=stations, favorites=favorites)


def find_station(station_list):
    i = 0
    for station in station_list:
        if ObjectId(station['_id']) == ObjectId(session['current_station']):
            return i
        i += 1
    return 0


@app.route('/register', methods=["GET", "POST"])
def register():
    # check if username already exists in db
    if request.method == "POST":
        existing_user = mongo.db.radiofilos.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        register_user = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.radiofilos.insert_one(register_user)
        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.radiofilos.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for("radio"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))
        else:
            # username doesn't exists
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.radiofilos.find_one(
        {"username": session["user"]})["username"]
    if session["user"]:
        return render_template("profile.html", username=username)
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    # session.pop("user")
    session['user'] = ""
    return redirect(url_for("login"))


# @app.route("/radio/<country>", methods=["GET", "POST"])
# def radio(country):
@app.route("/x")
def x():
    countries = list(mongo.db.countries.find().sort("name", 1))
    if request.method == "GET":
        stations = list(mongo.db.stations.find({'country': countries[0]["name"]}))
        station_info = {
            "country_name": stations[0]["country"],
            "station_id": ObjectId(stations[0]["_id"]),
            "url_resolved": stations[0]["url_resolved"],
            "station_name": stations[0]["name"],
            'homepage': stations[0]["homepage"],
            'favicon': stations[0]["favicon"],
            'tags': stations[0]["tags"],
        }
    else:
        stations = list(mongo.db.stations.find({'country': request.form.get("country_name")}))
        if request.form['selector'] == "form_station":
            station = mongo.db.stations.find_one({'_id': ObjectId(request.form.get("station_id"))})
            station_info = {
                "country_name": request.form.get("country_name"),
                "station_id": ObjectId(request.form.get("station_id")),
                "url_resolved": station["url_resolved"],
                "station_name": station["name"],
                'homepage': station["homepage"],
                'favicon': station["favicon"],
                'tags': station["tags"],
            }
        else:
            station_info = {
                "country_name": request.form.get("country_name"),
                "station_id": ObjectId(stations[0]["_id"]),
                "url_resolved": stations[0]["url_resolved"],
                "station_name": stations[0]["name"],
                'homepage': stations[0]["homepage"],
                'favicon': stations[0]["favicon"],
                'tags': stations[0]["tags"],
            }
    if session:
        favorites = list(mongo.db.favorites.find({'user': session['user']}))
    else:
        favorites = {}
    return render_template("radio.html", station_info=station_info,
                           countries=countries, stations=stations, favorites=favorites, )


app.run(debug=True)
