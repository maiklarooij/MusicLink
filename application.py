import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from collections import Counter
import json

from datetime import datetime
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
        shared_data =[]
        for followed in followinglist:
            shared_data.append(db.execute("SELECT * FROM shared WHERE userid=:userid", userid=followed['followeduserid']))
        shared_data.append(db.execute("SELECT * FROM shared WHERE userid=:myid", myid=session['user_id']))
        print(shared_data)
        return render_template("home.html", titles=titles, shared=shared_data)

    return render_template("home.html")


@app.route("/authorise", methods=["POST", "GET"])
def authorise():
    response = authentication.getUser()
    return redirect(response)

@app.route('/callback')
def callback():
    authentication.getUserToken(request.args['code'])
    if session.get("user_id") != None:
        oauth = authentication.getAccessToken()[0]
        spotify = spotipy.Spotify(auth=oauth)

        profilepic = spotify.current_user()["images"]
        if len(profilepic) == 0:
            profilepic = "https://genslerzudansdentistry.com/wp-content/uploads/2015/11/anonymous-user.png"
        else:
            profilepic = profilepic[0]['url']

        db.execute("UPDATE users SET profilepic = :profilepic WHERE userid = :userid", profilepic=profilepic, userid=session["user_id"])
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

            profilepic = spotify.current_user()["images"]
            if len(profilepic) == 0:
                profilepic = "https://genslerzudansdentistry.com/wp-content/uploads/2015/11/anonymous-user.png"
            else:
                profilepic = profilepic[0]['url']


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
        pictures = []
        track_result = dict()
        album_result = dict()
        artist_result = dict()
        duration = []
        input = request.form.get("search")
        searchtype = request.form.get("type")
        if searchtype == 'track':
            track_result = spotify.search(q='track:' + input, type=searchtype)
            print("search")
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

@app.route("/playlist", methods=["GET","POST"])
@login_required
def playlist():

    oauth = authentication.getAccessToken()[0]
    spotify = spotipy.Spotify(auth=oauth)

    # take top 5 tracks
    # take top 5 artists
    songs = []

    artists = list(db.execute ("SELECT artist1, artist2, artist3, artist4, artist5 FROM top WHERE userid=:id", id=session["user_id"])[0].values())
    tracks = list(db.execute("SELECT track1, track2, track3, track4, track5 FROM top WHERE userid=:id", id=session["user_id"])[0].values())

    recommendations = spotify.recommendations(seed_artists=random.sample(artists, 2), seed_tracks=random.sample(tracks, 3), limit=30)['tracks']
    titles = []
    for recommendation in recommendations:
        titles.append({'name': recommendation['name'], 'artists': [artist['name'] for artist in recommendation['artists']], 'img': recommendation['album']['images'][0]['url'], 'link': recommendation['uri']})
    # create
    if request.method == "POST":
        oauth = authentication.getAccessToken()[0]
        spotify = spotipy.Spotify(auth=oauth)
        spotifyid = db.execute("SELECT spotifyid FROM users where userid=:user_id", user_id=session["user_id"])[0]["spotifyid"]
        now = datetime.now() # current date and time
        now = now.strftime("%m/%d_%H:%M")
        name = 'MusicLink_'+ now
        playlist_id = spotify.user_playlist_create(user=spotifyid, name=name)['id']
        for song in recommendations:
            songs.append(song['uri'])
        spotify.user_playlist_add_tracks(user=spotifyid, playlist_id=playlist_id, tracks=songs)
        flash("Added to Spotify!")
    return render_template("playlist.html", titles=titles)

@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")

@app.route('/ownprofile', methods=["GET", "POST"])
@login_required
def ownprofile():
    oauth = authentication.getAccessToken()[0]
    spotify = spotipy.Spotify(auth=oauth)

    term = request.form.get("term")

    recenten = spotify.current_user_recently_played(limit=6)['items']
    top_artists = spotify.current_user_top_artists(limit=10, offset=0, time_range=term)["items"]
    top_tracks = spotify.current_user_top_tracks(limit=10, offset=0, time_range=term)["items"]
    top_artists = [artist["id"] for artist in top_artists]
    top_tracks = [track["id"] for track in top_tracks]

    top_genres = db.execute ("SELECT genre1, genre2, genre3 FROM top WHERE userid=:id", id=session["user_id"])

    recent = []
    for nummer in recenten:
        liedje = spotify.track(nummer['track']['id'])
        recent.append((liedje['album']['artists'][0]['name'], liedje['name'], liedje['album']['images'][0]['url']))

    genres = []
    for genre in top_genres[0]:
        genres.append(top_genres[0][genre])

    artists = []
    for artist in top_artists:
        artiest = spotify.artist(artist)
        artists.append((artiest['name'], artiest['images'][0]['url']))

    nummer_artiest = []
    for liedje in top_tracks:
        nummer = spotify.track(liedje)
        nummer_artiest.append((nummer['album']['artists'][0]['name'], nummer['name'], nummer['album']['images'][0]['url']))

    gebruikersnaam = db.execute("SELECT username FROM users WHERE userid=:id", id=session["user_id"])

    profilepic = db.execute("SELECT profilepic FROM users WHERE userid=:id", id=session["user_id"])[0]['profilepic']
    print(spotify.me())
    if request.method == "GET":
        return render_template("ownprofile.html", gebruikersnaam=gebruikersnaam[0]['username'],
        top_tracks=nummer_artiest, top_artists=artists, genres=genres, recent=recent, keuze='medium_term', profilepic=profilepic)
    elif request.method == "POST":
        return render_template("ownprofile.html", gebruikersnaam=gebruikersnaam[0]['username'],
        top_tracks=nummer_artiest, top_artists=artists, genres=genres, recent=recent, keuze=term, profilepic=profilepic)

@app.route('/friendssearch', methods=["GET"])
@login_required
def friendssearch():
    following = db.execute("SELECT followeduserid FROM following WHERE followuserid = :userid", userid=session["user_id"])
    following = [user['followeduserid'] for user in following]
    users = [user for user in db.execute("SELECT username, profilepic, userid FROM users")]
    users.remove(db.execute("SELECT username, profilepic, userid FROM users WHERE userid=:userid", userid=session['user_id'])[0])
    q = request.args.get("q")
    results = [user for user in users if q if user['username'].upper().startswith(q.upper())]
    return render_template("friendssearch.html", results=results, following=following)

@app.route('/friends', methods=["GET"])
@login_required
def friends():
    genres = db.execute("SELECT genre1, genre2, genre3 FROM top WHERE userid = :userid", userid=session["user_id"])
    following = db.execute("SELECT followeduserid FROM following WHERE followuserid = :userid", userid=session["user_id"])
    following = [user['followeduserid'] for user in following]

    samegenreusers = db.execute("SELECT userid, genre1, genre2, genre3 FROM top WHERE genre1 = :genre1 OR genre2 = :genre1 OR genre3 = :genre1 OR genre1 = :genre2 OR genre2 = :genre2 OR genre3 = :genre2 OR genre1 = :genre3 or genre2 = :genre3 OR genre3 = :genre3",
                    genre1=genres[0]['genre1'], genre2=genres[0]['genre2'], genre3=genres[0]['genre3'])

    samegenreusers = [user for user in samegenreusers if user['userid'] != session["user_id"]]
    samegenreusers = [user for user in samegenreusers if user['userid'] not in following]

    for user in samegenreusers:
        user['name'] = db.execute("SELECT username FROM users WHERE userid = :userid", userid=user['userid'])[0]['username']
        user['img'] = db.execute("SELECT profilepic FROM users WHERE userid = :userid", userid=user['userid'])[0]['profilepic']

    if len(samegenreusers) > 3:
        samegenreusers = random.sample(samegenreusers, 3)
    return render_template("friends.html", users=samegenreusers, following=following)

@app.route('/follow', methods=["POST"])
@login_required
def follow():
    oauth = authentication.getAccessToken()[0]
    spotify = spotipy.Spotify(auth=oauth)

    username = request.form.get('follow')
    usernameid = db.execute("SELECT userid FROM users WHERE username = :username", username=username)[0]['userid']
    if len(db.execute("SELECT followeduserid FROM following WHERE followuserid = :userid AND followeduserid = :followeduserid", userid=session['user_id'], followeduserid=usernameid)) == 0:
        db.execute("INSERT INTO following (followuserid, followeduserid) VALUES (:userid, :followeduserid)", userid=session['user_id'], followeduserid=usernameid)
        spotify.user_follow_users(ids=[db.execute("SELECT spotifyid FROM users WHERE userid= :followeduserid", followeduserid=usernameid)[0]['spotifyid']])
        flash(f"Successfully followed {username}!")
    else:
        db.execute("DELETE FROM following WHERE followeduserid = :usernameid AND followuserid = :userid", usernameid=usernameid, userid=session['user_id'])
        spotify.user_unfollow_users(ids=[db.execute("SELECT spotifyid FROM users WHERE userid= :followeduserid", followeduserid=usernameid)[0]['spotifyid']])
        flash(f"Successfully unfollowed {username}!")


    return redirect("/home")

@app.route('/settings')
@login_required
def settings():
    return render_template("settings.html")

@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """Let's the user change the password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure old password, new password and confirmation were submitted
        if not request.form.get("oldpass") or not request.form.get("newpass") or not request.form.get("confirmation"):
            return apology("fill in all fields")

        # Ensure that the old password is the same as currently stored in database
        elif not check_password_hash(db.execute("SELECT hash FROM users WHERE userid = :userid", userid=session["user_id"])[0]["hash"], request.form.get("oldpass")):
            return apology("old password wrong")

        # Ensure that old and new password are not the same
        elif request.form.get("oldpass") == request.form.get("newpass"):
            return apology("choose a new password")

        # Ensure that new password and confirmation match
        elif request.form.get("newpass") != request.form.get("confirmation"):
            return apology("the passwords do not match")

        # Update the users password
        db.execute("UPDATE users SET hash = :password", password=generate_password_hash(request.form.get("newpass")))

        # Redirect user to home page
        return redirect("/ownprofile")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepassword.html")

@app.route("/changeusername", methods=["GET", "POST"])
@login_required
def changeusername():
    """Let's the user change the username"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = db.execute("SELECT username FROM users WHERE userid = :userid", userid=session["user_id"])
        print(username)
        # Ensure old password, new password and confirmation were submitted
        if not request.form.get("password") or not request.form.get("newusername"):
            return apology("Fill in all fields")

        # Ensure that the old password is the same as currently stored in database
        elif not check_password_hash(db.execute("SELECT hash FROM users WHERE userid = :userid", userid=session["user_id"])[0]["hash"], request.form.get("password")):
            return apology("Password wrong")

        # Ensure that old and new username are not the same
        if request.form.get("newusername") == username[0]['username']:
            return apology("Choose a new username")

        # Update the users password
        db.execute("UPDATE users SET username = :username WHERE userid = :userid", username=request.form.get("newusername"), userid=session["user_id"])

        # Redirect user to home page
        return redirect("/ownprofile")

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        return render_template("changeusername.html")



@app.route("/share", methods=["GET", "POST"])
@login_required
def Share():
    if request.method == 'POST':
        value = request.form.get("sharedtext")
        username = db.execute("SELECT username FROM users WHERE userid = ?", session["user_id"])[0]['username']
        db.execute("INSERT into shared (userid, value, username) VALUES (:userid, :value, :username)", userid=session["user_id"], value=value, username=username)
        flash("Shared!")
        return redirect("/home")
    return render_template("share.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    oauth = authentication.getAccessToken()[0]
    spotify = spotipy.Spotify(auth=oauth)

    username = request.form.get("username")
    userid = db.execute("SELECT userid FROM users WHERE username=:username", username=username)[0]['userid']
    following = db.execute("SELECT followeduserid FROM following WHERE followuserid = :userid", userid=session["user_id"])
    following = [user['followeduserid'] for user in following]
    top_artists = db.execute ("SELECT artist1, artist2, artist3, artist4, artist5 FROM top WHERE userid=:id", id=userid)
    top_tracks = db.execute ("SELECT track1, track2, track3, track4, track5 FROM top WHERE userid=:id", id=userid)
    top_genres = db.execute ("SELECT genre1, genre2, genre3 FROM top WHERE userid=:id", id=userid)

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

    profilepic = db.execute("SELECT profilepic FROM users WHERE userid=:id", id=userid)[0]['profilepic']

    if request.method == "GET":
        return render_template("profile.html", gebruikersnaam=username, top_tracks=nummer_artiest,
        top_artists=artists, genres=genres, profilepic=profilepic, following=following, userid=userid)
    elif request.method == "POST":
        return render_template("profile.html", gebruikersnaam=username, top_tracks=nummer_artiest,
        top_artists=artists, genres=genres, profilepic=profilepic, following=following, userid=userid)