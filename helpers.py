from flask import redirect, render_template, request, session
from functools import wraps
from collections import Counter
from cs50 import SQL

import os
import authentication
import spotipy

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

    db.execute("UPDATE top SET artist1 = :artist1, artist2 = :artist2, artist3 = :artist3, artist4 = :artist4, artist5 = :artist5 WHERE userid = :userid",
                artist1=top_artists[0], artist2=top_artists[1], artist3=top_artists[2], artist4=top_artists[3], artist5=top_artists[4], userid=session["user_id"])

    db.execute("UPDATE top SET track1 = :track1, track2 = :track2, track3 = :track3, track4 = :track4, track5 = :track5 WHERE userid = :userid",
                track1=top_tracks[0], track2=top_tracks[1], track3=top_tracks[2], track4=top_tracks[3], track5=top_tracks[4], userid=session["user_id"])

    db.execute("UPDATE top SET genre1 = :genre1, genre2 = :genre2, genre3 = :genre3 WHERE userid = :userid",
                genre1=genres[0], genre2=genres[1], genre3=genres[2], userid=session["user_id"])