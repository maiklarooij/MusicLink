from flask import redirect, render_template, request, session
from functools import wraps
from collections import Counter
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash

import os
import authentication
import spotipy
import random

db = SQL("sqlite:///musiclink.db")

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def update_database_top(spotify):

    top_artists = spotify.current_user_top_artists(limit=20, offset=0, time_range='short_term')["items"]

    if len(top_artists) < 5:
        top_artists = spotify.current_user_top_artists(limit=20, offset=0, time_range='medium_term')["items"]
        if len(top_artists) < 5:
            top_artists = spotify.current_user_top_artists(limit=20, offset=0, time_range='long_term')["items"]

    top_tracks = spotify.current_user_top_tracks(limit=5, offset=0, time_range='short_term')["items"]

    if len(top_tracks) < 5:
        top_tracks = spotify.current_user_top_tracks(limit=5, offset=0, time_range='medium_term')["items"]
        if len(top_tracks) < 5:
            top_tracks = spotify.current_user_top_tracks(limit=5, offset=0, time_range='long_term')["items"]

    genrelists = [artist["genres"] for artist in top_artists]
    genres = []
    for genrelist in genrelists:
        for genre in genrelist:
            genres.append(genre)

    genres = [genre[0] for genre in Counter(genres).most_common(3)]

    top_artists = [artist["id"] for artist in top_artists][:5]
    top_tracks = [track["id"] for track in top_tracks]

    db.execute("UPDATE top SET artist1 = :artist1, artist2 = :artist2, artist3 = :artist3, artist4 = :artist4, artist5 = :artist5, " \
                "track1 = :track1, track2 = :track2, track3 = :track3, track4 = :track4, track5 = :track5, " \
                "genre1 = :genre1, genre2 = :genre2, genre3 = :genre3 " \
                "WHERE userid = :userid",
                artist1=top_artists[0], artist2=top_artists[1], artist3=top_artists[2], artist4=top_artists[3], artist5=top_artists[4],
                track1=top_tracks[0], track2=top_tracks[1], track3=top_tracks[2], track4=top_tracks[3], track5=top_tracks[4],
                genre1=genres[0], genre2=genres[1], genre3=genres[2], userid=session["user_id"])

def get_following():
    followinglist = db.execute("SELECT followeduserid FROM following WHERE followuserid = :userid", userid=session['user_id'])
    if len(followinglist) != 0:
        following = []
        for followed in followinglist:
            following.append(followed['followeduserid'])

    return following

def get_friends_recommendations(spotify, following):

    tracks = []
    for userid in following:
        for i in range(1, 6):
            track = "track" + str(i)
            tracks.append(db.execute("SELECT " + track  + " FROM top WHERE userid = :userid", userid=userid)[0][track])

    recommendations = spotify.recommendations(seed_tracks=random.sample(tracks, 5), limit=10)['tracks']

    tracks = []
    for recommendation in recommendations:
        tracks.append({'name': recommendation['name'], 'artists': [artist['name'] for artist in recommendation['artists']], 'img': recommendation['album']['images'][0]['url'], 'link': recommendation['uri']})

    return tracks


def get_feed(spotify, following):
    following.append(session["user_id"])

    messages = db.execute("SELECT * FROM shared")
    feed = []
    for message in messages:
        if message['userid'] in following:
            feed.append(message)

    for message in feed:
        message['trackinfo'] = spotify.track(message['spotifyid'])
        message['profilepic'] = db.execute("SELECT profilepic FROM users WHERE userid = :userid", userid=message['userid'])[0]['profilepic']
    feed = sorted(feed, key=lambda x: x['time'], reverse=True)

    return feed


def update_profilepic(spotify):
    profilepic = spotify.current_user()["images"]
    if len(profilepic) == 0:
        profilepic = "https://genslerzudansdentistry.com/wp-content/uploads/2015/11/anonymous-user.png"
    else:
        profilepic = profilepic[0]['url']

    db.execute("UPDATE users SET profilepic = :profilepic WHERE userid = :userid", profilepic=profilepic, userid=session["user_id"])


def register_user(spotify):
    spotify_id = spotify.current_user()["id"]

    profilepic = spotify.current_user()["images"]

    if len(profilepic) == 0:
        profilepic = "https://genslerzudansdentistry.com/wp-content/uploads/2015/11/anonymous-user.png"
    else:
        profilepic = profilepic[0]['url']


    db.execute("INSERT INTO users (username, hash, spotifyid, profilepic) VALUES (:username, :password, :spotifyid, :profilepic)",
                username=request.form.get("username"), password=generate_password_hash(request.form.get("password"),
                method='pbkdf2:sha256', salt_length=8), spotifyid=spotify_id, profilepic=profilepic)

    rows = db.execute("SELECT * FROM users WHERE username = :username",
                  username=request.form.get("username"))

    session["user_id"] = rows[0]["userid"]

    db.execute("INSERT INTO top (userid) VALUES (:userid)", userid=session["user_id"])


def search_spotify(spotify, input, searchtype):

    if searchtype == 'track':
        searchresults = spotify.search(q='track:' + input, type=searchtype)
    elif searchtype == "artist":
        searchresults = spotify.search(q='artist:' + input, type=searchtype)
    elif searchtype == 'album':
        searchresults = spotify.search(q='album:' + input, type=searchtype)

    return searchresults