import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import *

import spotipy
import authorization

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
    """ Page where users can choose to register their account or log in to existing accounts """

    # Logs out the user before accessing start page
    session.clear()

    # Render start template
    return render_template("start.html")


@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    """ Displays the home page with a friends feed and track recommendations
        based on who the user follows """

    # Get Spotify OAuth token
    spotify = authorization.getSpotipy()

    # Store top 5 songs, artists and genres from user in database
    update_database_top(spotify)

    # Get a list of id's that the user is following
    following = get_following()

    # Get recommendations based on following users
    recommendations = get_friends_recommendations(spotify, following)

    # Get the shared messages from people the user follows
    feed = get_feed(spotify, following)
    # Render home template
    return render_template("home.html", recommendations=recommendations, feed=feed)


@app.route("/authorise", methods=["POST", "GET"])
def authorise():
    """ Gets Spotify authorisation """

    response = authorization.getUser()

    # Redirect to callback
    return redirect(response)

@app.route('/callback')
def callback():
    """ Redirected to after Spotify authorisation, redirects to home or register page """

    # Get Spotify user token
    authorization.getUserToken(request.args['code'])

    # If there is someone logged in
    if session.get("user_id") != None:

        # Get Spotify OAuth token
        spotify = authorization.getSpotipy()

        # Update profilepic with photo from Spotify
        update_profilepic(spotify)

        # Redirect to home
        return redirect("/home")

    # Else if no one is logged in, redirect to register a new user
    else:
        return redirect("/register")

@app.route('/register', methods=["POST", "GET"])
def register():
    """ Register new user """

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username and password were submitted, password and confirmation must match
        if not request.form.get("username") or not request.form.get("password") or request.form.get("password") != request.form.get("confirmation"):
            return apology("please fill in all fields")

        # Ensure that the username is not taken
        if len(db.execute("SELECT * FROM users WHERE username = :username",
            username=request.form.get("username"))) != 0:
            return apology("username already exists")
        # Get Spotify OAuth token
        spotify = authorization.getSpotipy()

        # Register new user
        register_user(spotify)
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


@app.route('/search', methods=["GET"])
@login_required
def search():
    """ Search for Spotify tracks, artists and albums """

    # Show search template
    return render_template("search.html")

@app.route('/searched', methods=["GET"])
@login_required
def searched():
    """ Gets search results """

    # Get Spotify OAuth token
    spotify = authorization.getSpotipy()

    # Get user search query
    input = request.args.get("q")
    searchtype = request.args.get("searchtype")

    print(input, searchtype)

    # Get search result from Spotify
    searchresults = search_spotify(spotify, input, searchtype)

    # Show results
    return render_template("searched.html", searchresults=searchresults, searchtype=searchtype)


@app.route("/playlist", methods=["GET", "POST"])
@login_required
def playlist():
    """ Generates a playlist based on listening habits """

    # Get Spotify OAuth token
    spotify = authorization.getSpotipy()

    # User reached route via GET (as by clicking a link or via redirect) or via selecting tracks&artists as dependent variable
    if request.method == "GET" or request.form['action'] == 'tracks&artists':

        # Define globals to use later
        global tracks
        global track_ids

        # Generate a personal playlist
        tracks, track_ids, dependent = generate_playlist(spotify,'both')

    elif request.form['action'] == 'tracks':
        # Generate a personal playlist
        tracks, track_ids, dependent = generate_playlist(spotify, 'tracks')

    elif request.form['action'] == 'artists':
        # Generate a personal playlist
        tracks, track_ids, dependent = generate_playlist(spotify, 'artists')

    # When clicked on 'export playlist'
    elif request.form['action'] == 'otherpage':

        return render_template("spotify_add.html")

            # Show template with the same playlist again
    elif request.form['action'] == 'addSpotify':
                # Export playlist to Spotify
        export_playlist(spotify, track_ids)
            # Show template with playlist
        return render_template("playlist.html", titles=tracks, alert='on')
    # Show template with playlist
    return render_template("playlist.html", titles=tracks, dependent=dependent)


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")

@app.route('/ownprofile', methods=["GET", "POST"])
@login_required
def ownprofile():
    """ Shows users listening statistics """

    # Get Spotify OAuth token
    spotify = authorization.getSpotipy()

    # Standard term is medium term, when chosen different by user, use this
    if request.method == "GET":
        term = 'medium_term'
    else:
        term = request.form.get("term")

    # Let the function know this is the current users profile
    profile = 'own'

    # Get statistics from Spotify
    recent, genres, artists, tracks, username, profilepic = get_statistics(spotify, term, None, profile)
    following = db.execute("SELECT * FROM following WHERE followuserid=:id", id=session["user_id"])
    followers = db.execute("SELECT * FROM following WHERE followeduserid=:id", id=session["user_id"])
    # Render template which shows personal statistics
    return render_template("ownprofile.html", username=username, following=len(following), followers=len(followers),
    top_tracks=tracks, top_artists=artists, genres=genres, recent=recent, term=term, profilepic=profilepic)


@app.route('/friends', methods=["GET"])
@login_required
def friends():
    """ Find and follow users """

    # Get users that are followed by active user
    following = get_following()

    # Generate a list of potential friends based on genre
    potential_friends = get_potential_friends(following)

    # Render template friends
    return render_template("friends.html", potential_friends=potential_friends, following=following)


@app.route('/followinglist', methods=["GET"])
@login_required
def followinglist():
    followinglist = db.execute("SELECT followeduserid FROM following WHERE followuserid=:id", id=session["user_id"])
    users = []
    for user in followinglist:
        users.append(db.execute("SELECT * FROM users WHERE userid=:user", user=user['followeduserid'])[0])
    return render_template("following.html", followinglist=users)

@app.route('/followerslist', methods=["GET"])
@login_required
def followerslist():
    followinglist = db.execute("SELECT followeduserid FROM following WHERE followuserid=:id", id=session["user_id"])
    following = [user['followeduserid'] for user in followinglist]

    followerslist = db.execute("SELECT followuserid FROM following WHERE followeduserid=:id", id=session["user_id"])
    users = []
    for user in followerslist:
        users.append(db.execute("SELECT * FROM users WHERE userid=:user", user=user['followuserid'])[0])

    return render_template("followers.html", followerslist=users, following=following)

@app.route('/friendssearch', methods=["GET"])
@login_required
def friendssearch():
    """ Shows search results for friends """

    # Get users that are followed by active user
    following = get_following()

    # Get search result
    results = search_friends()

    # Show search result
    return render_template("friendssearch.html", results=results, following=following)


@app.route('/follow', methods=["POST"])
@login_required
def follow():
    """ (Un)follow user """

    # Get Spotify OAuth token
    spotify = authorization.getSpotipy()

    # Get id from clicked user
    username = request.form.get('follow')

    # Follow (or unfollow when already followed) user
    follow_user(spotify, username)

    # Redirect to home page
    return redirect("/home")


@app.route('/settings')
@login_required
def settings():
    """ Shows settings """

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

        # Select username of active user
        username = db.execute("SELECT username FROM users WHERE userid = :userid", userid=session["user_id"])[0]['username']

        # Ensure password and new username are submitted
        if not request.form.get("password") or not request.form.get("newusername"):
            return apology("Fill in all fields")

        # Ensure that that password matches stored password
        elif not check_password_hash(db.execute("SELECT hash FROM users WHERE userid = :userid", userid=session["user_id"])[0]["hash"], request.form.get("password")):
            return apology("Password wrong")

        # Ensure that old and new username are not the same
        if request.form.get("newusername") == username:
            return apology("Choose a new username")

        # Update the users username
        db.execute("UPDATE users SET username = :username WHERE userid = :userid", username=request.form.get("newusername"), userid=session["user_id"])

        # Redirect user to home page
        return redirect("/ownprofile")

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        return render_template("changeusername.html")



@app.route("/share", methods=["GET", "POST"])
@login_required
def share():
    """ Users can share songs with their followers """

    # User clicked the submit button
    if request.method == 'POST':

        # Share the song
        share_post()
        flash("Shared!")

        # Redirect to home page
        return redirect("/home")

    # User reached route via GET by clicking a 'share' button
    else:

        # Get Spotify OAuth token
        spotify = authorization.getSpotipy()

        # Get details from song that is shared
        track = spotify.track(request.args.get("share"))
        artists = [artist['name'] for artist in track['artists']]

        # Render page where user can share the song with a custom message
        return render_template("share.html", track=track, artists=artists)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """ Gets a profile of a user with their listening statistics """

    # Get Spotify OAuth token
    spotify = authorization.getSpotipy()

    print(request.form.get("username"))

    # Get userid of the clicked user
    userid = db.execute("SELECT userid FROM users WHERE username=:username", username=request.form.get('username'))[0]['userid']

    # Get users that are followed by active user
    following = get_following()

    # Let the function know this is the profile of an other user
    profile = 'other'

    # Get statistics from the user
    recent, genres, artists, tracks, username, profilepic = get_statistics(spotify, None, userid, profile)

    # Show statistics
    return render_template("profile.html", username=username, top_tracks=tracks,
    top_artists=artists, genres=genres, profilepic=profilepic, following=following, userid=userid)