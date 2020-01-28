import base64, json, requests
import spotipy

#Add your client ID
CLIENT_ID = "e351ac3d72594cad83fa632150e602df"

#aDD YOUR CLIENT SECRET FROM SPOTIFY
CLIENT_SECRET = "80dd7e7676fb4a8ca76cedf2e417b57e"


redirect_uri = "https://4159dc31-c71b-4bb9-acfc-6c04c02e08a9-ide.cs50.xyz:8080/callback"


#Add needed scope from spotify user
SCOPE = "streaming user-read-email user-read-private user-read-currently-playing user-read-recently-played user-top-read playlist-modify-public user-follow-modify"
#token_data will hold authentication header with access code, the allowed scopes, and the refresh countdown
TOKEN_DATA = []


SPOTIFY_URL_AUTH = 'https://accounts.spotify.com/authorize/?'
SPOTIFY_URL_TOKEN = 'https://accounts.spotify.com/api/token/'
RESPONSE_TYPE = 'code'
HEADER = 'application/x-www-form-urlencoded'
REFRESH_TOKEN = ''

def getAuth(client_id, redirect_uri, scope):
    data = "{}client_id={}&response_type=code&redirect_uri={}&scope={}".format(SPOTIFY_URL_AUTH, client_id, redirect_uri, scope)
    return data

def getToken(code, client_id, client_secret, redirect_uri):
    body = {
        "grant_type": 'authorization_code',
        "code" : code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }

    auth_str = f"{client_id}:{client_secret}"
    encoded = base64.urlsafe_b64encode(auth_str.encode()).decode()
    headers = {"Content-Type" : HEADER, "Authorization" : "Basic {}".format(encoded)}

    post = requests.post(SPOTIFY_URL_TOKEN, params=body, headers=headers)
    return handleToken(json.loads(post.text))

def handleToken(response):
    auth_head = {"Authorization": "Bearer {}".format(response["access_token"])}
    REFRESH_TOKEN = response["refresh_token"]
    return [response["access_token"], auth_head, response["scope"], response["expires_in"]]

def refreshAuth():
    body = {
        "grant_type" : "refresh_token",
        "refresh_token" : REFRESH_TOKEN
    }

    post_refresh = requests.post(SPOTIFY_URL_TOKEN, data=body, headers=HEADER)
    p_back = json.dumps(post_refresh.text)

    return handleToken(p_back)


def getUser():
    return getAuth(CLIENT_ID, redirect_uri, SCOPE)

def getUserToken(code):
    global TOKEN_DATA
    TOKEN_DATA = getToken(code, CLIENT_ID, CLIENT_SECRET, redirect_uri)

def refreshToken(time):
    time.sleep(time)
    TOKEN_DATA = refreshAuth()

def getAccessToken():
    return TOKEN_DATA

def getSpotipy():
    oauth = getAccessToken()[0]
    spotify = spotipy.Spotify(auth=oauth)
    return spotify