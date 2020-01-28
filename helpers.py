from flask import redirect, render_template, request, session, flash
from functools import wraps
from collections import Counter
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from random import shuffle

import os
import authorization
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

    following = []
    if len(followinglist) != 0:
        following = [followed['followeduserid'] for followed in followinglist]


    return following

def get_friends_recommendations(spotify, following):

    tracks = []

    if len(following) != 0:
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


def generate_playlist(spotify, dependent):
    if dependent == 'tracks':
        # Get users top 5 tracks
        tracks = list(db.execute("SELECT track1, track2, track3, track4, track5 FROM top WHERE userid=:id", id=session["user_id"])[0].values())
        recommendations = spotify.recommendations(seed_tracks=tracks, limit=30)['tracks']

    elif dependent == 'artists':

        # Get users top 5 artists
        artists = list(db.execute("SELECT artist1, artist2, artist3, artist4, artist5 FROM top WHERE userid=:id", id=session["user_id"])[0].values())
        recommendations = spotify.recommendations(seed_artists=artists, limit=30)['tracks']
    else:
        # Get users top 5 tracks
        tracks = list(db.execute("SELECT track1, track2, track3, track4, track5 FROM top WHERE userid=:id", id=session["user_id"])[0].values())
        recommendations_a = spotify.recommendations(seed_tracks=tracks, limit=15)['tracks']

        # Get users top 5 artists
        artists = list(db.execute("SELECT artist1, artist2, artist3, artist4, artist5 FROM top WHERE userid=:id", id=session["user_id"])[0].values())
        recommendations_b = spotify.recommendations(seed_artists=artists, limit=15)['tracks']
        recommendations = recommendations_a + recommendations_b
        shuffle(recommendations)
    titles = [{'name': recommendation['name'], 'artists': [artist['name'] for artist in recommendation['artists']], 'img': recommendation['album']['images'][0]['url'], 'link': recommendation['uri']} for recommendation in recommendations]
    track_ids = [recommendation['id'] for recommendation in recommendations]
    return titles, track_ids, dependent


def export_playlist(spotify, track_ids):

    spotifyid = db.execute("SELECT spotifyid FROM users where userid=:user_id", user_id=session["user_id"])[0]["spotifyid"]
    name = request.form.get("playlistName")
    if not name:
        today = date.today().strftime("%d/%m/%Y")
        name = 'MusicLink_'+ today

    playlist_id = spotify.user_playlist_create(user=spotifyid, name=name)['id']
    spotify.user_playlist_add_tracks(user=spotifyid, playlist_id=playlist_id, tracks=track_ids)


def get_statistics(spotify, term, userid, profile):

    if profile == 'other':
        recent_tracks = []
        top_artists = list(db.execute ("SELECT artist1, artist2, artist3, artist4, artist5 FROM top WHERE userid=:id", id=userid)[0].values())
        top_tracks = list(db.execute ("SELECT track1, track2, track3, track4, track5 FROM top WHERE userid=:id", id=userid)[0].values())
        genres = list(db.execute ("SELECT genre1, genre2, genre3 FROM top WHERE userid=:id", id=userid)[0].values())
        username = db.execute("SELECT username FROM users WHERE userid=:id", id=userid)[0]['username']
        profilepic = db.execute("SELECT profilepic FROM users WHERE userid=:id", id=userid)[0]['profilepic']
    else:
        recent_tracks = spotify.current_user_recently_played(limit=6)['items']
        top_artists = [artist["id"] for artist in spotify.current_user_top_artists(limit=10, offset=0, time_range=term)["items"]]
        top_tracks = [track["id"] for track in spotify.current_user_top_tracks(limit=10, offset=0, time_range=term)["items"]]
        genres = db.execute ("SELECT genre1, genre2, genre3 FROM top WHERE userid=:id", id=session["user_id"])[0].values()
        username = db.execute("SELECT username FROM users WHERE userid=:id", id=session["user_id"])[0]['username']

        profilepic = db.execute("SELECT profilepic FROM users WHERE userid=:id", id=session["user_id"])[0]['profilepic']


    recent = []
    for track in recent_tracks:
        recent_track = spotify.track(track['track']['id'])
        recent.append((recent_track['album']['artists'][0]['name'], recent_track['name'], recent_track['album']['images'][0]['url']))

    artists = []
    for artist in top_artists:
        fav_artist = spotify.artist(artist)
        artists.append((fav_artist['name'], fav_artist['images'][0]['url']))

    tracks = []
    for track in top_tracks:
        fav_track = spotify.track(track)
        tracks.append((fav_track['album']['artists'][0]['name'], fav_track['name'], fav_track['album']['images'][0]['url']))


    return recent, genres, artists, tracks, username, profilepic


def get_potential_friends(following):

    genres = db.execute("SELECT genre1, genre2, genre3 FROM top WHERE userid = :userid", userid=session["user_id"])

    samegenreusers = db.execute("SELECT userid, genre1, genre2, genre3 FROM top WHERE genre1 = :genre1 OR genre2 = :genre1 OR genre3 = :genre1 OR genre1 = :genre2 OR genre2 = :genre2 OR genre3 = :genre2 OR genre1 = :genre3 or genre2 = :genre3 OR genre3 = :genre3",
                    genre1=genres[0]['genre1'], genre2=genres[0]['genre2'], genre3=genres[0]['genre3'])

    samegenreusers = [user for user in samegenreusers if user['userid'] != session["user_id"]]
    samegenreusers = [user for user in samegenreusers if user['userid'] not in following]

    for user in samegenreusers:
        user['name'] = db.execute("SELECT username FROM users WHERE userid = :userid", userid=user['userid'])[0]['username']
        user['img'] = db.execute("SELECT profilepic FROM users WHERE userid = :userid", userid=user['userid'])[0]['profilepic']

    if len(samegenreusers) > 3:
        samegenreusers = random.sample(samegenreusers, 3)

    return samegenreusers


def search_friends():
    users = [user for user in db.execute("SELECT username, profilepic, userid FROM users")]
    users.remove(db.execute("SELECT username, profilepic, userid FROM users WHERE userid=:userid", userid=session['user_id'])[0])
    q = request.args.get("q")
    results = [user for user in users if q if user['username'].upper().startswith(q.upper())]

    return results


def follow_user(spotify, username):

    usernameid = db.execute("SELECT userid FROM users WHERE username = :username", username=username)[0]['userid']

    if len(db.execute("SELECT followeduserid FROM following WHERE followuserid = :userid AND followeduserid = :followeduserid", userid=session['user_id'], followeduserid=usernameid)) == 0:
        db.execute("INSERT INTO following (followuserid, followeduserid) VALUES (:userid, :followeduserid)", userid=session['user_id'], followeduserid=usernameid)
        spotify.user_follow_users(ids=[db.execute("SELECT spotifyid FROM users WHERE userid= :followeduserid", followeduserid=usernameid)[0]['spotifyid']])
        flash(f"Successfully followed {username}!")
    else:
        db.execute("DELETE FROM following WHERE followeduserid = :usernameid AND followuserid = :userid", usernameid=usernameid, userid=session['user_id'])
        spotify.user_unfollow_users(ids=[db.execute("SELECT spotifyid FROM users WHERE userid= :followeduserid", followeduserid=usernameid)[0]['spotifyid']])
        flash(f"Successfully unfollowed {username}!")


def share_post():

    value = request.form.get("sharedtext")
    username = db.execute("SELECT username FROM users WHERE userid = :userid", userid=session["user_id"])[0]['username']
    db.execute("INSERT into shared (userid, value, username, spotifyid) VALUES (:userid, :value, :username, :spotifyid)", userid=session["user_id"], value=value, username=username, spotifyid=request.form.get("trackid"))