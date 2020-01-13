from flask_spotify_auth import getAuth, refreshAuth, getToken

#Add your client ID
CLIENT_ID = "e351ac3d72594cad83fa632150e602df"

#aDD YOUR CLIENT SECRET FROM SPOTIFY
CLIENT_SECRET = "80dd7e7676fb4a8ca76cedf2e417b57e"

#Port and callback url can be changed or ledt to localhost:5000
redirect_uri = "https://aed7133f-13a0-4d3f-89bc-a0dea558ee71-ide.cs50.xyz:8080/callback"

#Add needed scope from spotify user
SCOPE = "streaming user-read-email user-read-private user-read-currently-playing user-read-recently-played user-top-read"
#token_data will hold authentication header with access code, the allowed scopes, and the refresh countdown
TOKEN_DATA = []


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
