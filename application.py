import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from collections import Counter

import random
import spotipy
import authentication
from helpers import login_required, apology, update_database_top

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///musiclink.db")


@app.route("/", methods=["GET"])
def start():
    session.clear()

    return render_template("start.html")

@app.route("/home", methods=["GET", "POST"])
@login_required
def home():

    oauth = authentication.getAccessToken()[0]
    spotify = spotipy.Spotify(auth=oauth)

    update_database_top(spotify)

    followinglist = db.execute("SELECT followeduserid FROM following WHERE followuserid = :userid", userid=session['user_id'])
    if len(followinglist) != 0:
        following = []
        for followed in followinglist:
            following.append(followed['followeduserid'])

        tracks = []
        for userid in following:
            tracks.append(db.execute("SELECT track1 FROM top WHERE userid = :userid", userid=userid)[0]['track1'])
            tracks.append(db.execute("SELECT track2 FROM top WHERE userid = :userid", userid=userid)[0]['track2'])
            tracks.append(db.execute("SELECT track3 FROM top WHERE userid = :userid", userid=userid)[0]['track3'])
            tracks.append(db.execute("SELECT track4 FROM top WHERE userid = :userid", userid=userid)[0]['track4'])
            tracks.append(db.execute("SELECT track5 FROM top WHERE userid = :userid", userid=userid)[0]['track5'])

        recommendations = spotify.recommendations(seed_tracks=random.sample(tracks, 5), limit=10)['tracks']
        titles = []
        for recommendation in recommendations:
            titles.append({'name': recommendation['name'], 'artists': [artist['name'] for artist in recommendation['artists']], 'img': recommendation['album']['images'][0]['url'], 'link': recommendation['uri']})

        return render_template("home.html", titles=titles)

    return render_template("home.html")


@app.route("/authorise", methods=["POST", "GET"])
def authorise():
    response = authentication.getUser()
    return redirect(response)

@app.route('/callback')
def callback():
    authentication.getUserToken(request.args['code'])
    if session.get("user_id") != None:
        return redirect("/home")
    else:
        return redirect("/register")

@app.route('/register', methods=["POST", "GET"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username and password were submitted, password and confirmation must match
        if not request.form.get("username") or not request.form.get("password") or request.form.get("password") != request.form.get("confirmation"):
            return apology("please fill in all fields")

        # Ensure that the username is not taken
        if len(db.execute("SELECT * FROM users WHERE username = :username",
            username=request.form.get("username"))) != 0:
            return apology("username already exists")

        # Insert the username and hashed password into users database
        else:
            oauth = authentication.getAccessToken()[0]
            spotify = spotipy.Spotify(auth=oauth)

            spotify_id = spotify.current_user()["id"]

            db.execute("INSERT INTO users (username, hash, spotifyid) VALUES (:username, :password, :spotifyid)",
                        username=request.form.get("username"), password=generate_password_hash(request.form.get("password"),
                        method='pbkdf2:sha256', salt_length=8), spotifyid=spotify_id)

            rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

            session["user_id"] = rows[0]["userid"]

            db.execute("INSERT INTO top (userid) VALUES (:userid)", userid=session["user_id"])


        flash('Succesfully registered!')
        # Redirect user to home page
        return redirect("/home")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["userid"]

        # Redirect user to home page
        return redirect("/authorise")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route('/search', methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        oauth = authentication.getAccessToken()[0]
        spotify = spotipy.Spotify(auth=oauth)
        artists = []
        pictures = []
        track_result = dict()
        album_result = dict()
        artist_result = dict()
        duration = []
        input = request.form.get("search")
        searchtype = request.form.get("type")
        if searchtype == 'track':
            track_result = spotify.search(q='track:' + input, type=searchtype)
        elif searchtype == "artist":
            artist_result = spotify.search(q='artist:' + input, type=searchtype)
        elif searchtype == 'album':
            album_result = spotify.search(q='album:' + input, type=searchtype)
        if not artist_result:
            if not track_result:
                if not album_result:
                    return apology("No results", 404)

        return render_template("searched.html", track_result=track_result, artist_result=artist_result,
                                album_result=album_result, pictures=pictures, duration=duration)

    else:
        return render_template("search.html")

@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")

@app.route('/ownprofile')
@login_required
def ownprofile():
    oauth = authentication.getAccessToken()[0]
    spotify = spotipy.Spotify(auth=oauth)

    top_tracks = db.execute ("SELECT track1, track2, track3, track4, track5 FROM top WHERE userid=:id", id=session["user_id"])
    top_artists = db.execute ("SELECT artist1, artist2, artist3, artist4, artist5 FROM top WHERE userid=:id", id=session["user_id"])
    top_genres = db.execute ("SELECT genre1, genre2, genre3 FROM top WHERE userid=:id", id=session["user_id"])

    genres = []
    for genre in top_genres[0]:
        genres.append(top_genres[0][genre])

    artists = []
    for artist in top_artists[0]:
        artiest = spotify.artist(top_artists[0][artist])
        artists.append((artiest['name'], artiest['images'][0]['url']))

    nummer_artiest = []
    for liedje in top_tracks[0]:
        nummer = spotify.track(top_tracks[0][liedje])
        nummer_artiest.append((nummer['album']['artists'][0]['name'], nummer['name'], nummer['album']['images'][0]['url']))

    gebruikersnaam = db.execute("SELECT username FROM users WHERE userid=:id", id=session["user_id"])
    return render_template("ownprofile.html", gebruikersnaam=gebruikersnaam[0]['username'], top_tracks=nummer_artiest, top_artists=artists, genres=genres)


@app.route('/friendssearch', methods=["GET"])
@login_required
def friendssearch():
    users = [user["username"] for user in db.execute("SELECT username FROM users")]
    users.remove(db.execute("SELECT username FROM users WHERE userid=:userid", userid=session['user_id'])[0]['username'])
    q = request.args.get("q")
    results = [user for user in users if q if user.upper().startswith(q.upper())]
    return render_template("friendssearch.html", results=results)

@app.route('/friends', methods=["GET"])
@login_required
def friends():
    return render_template("friends.html")

@app.route('/follow', methods=["POST"])
@login_required
def follow():
    username = request.form.get('follow')
    usernameid = db.execute("SELECT userid FROM users WHERE username = :username", username=username)[0]['userid']
    if len(db.execute("SELECT followeduserid FROM following WHERE followuserid = :userid AND followeduserid = :followeduserid", userid=session['user_id'], followeduserid=usernameid)) == 0:
        db.execute("INSERT INTO following (followuserid, followeduserid) VALUES (:userid, :followeduserid)", userid=session['user_id'], followeduserid=usernameid)
        flash(f"Successfully followed {username}!")
    else:
        db.execute("DELETE FROM following WHERE followeduserid = :usernameid AND followuserid = :userid", usernameid=usernameid, userid=session['user_id'])
        flash(f"Successfully unfollowed {username}!")
    return redirect("/home")

@app.route('/settings')
@login_required
def settings():
    return render_template("settings.html")