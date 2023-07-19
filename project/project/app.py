from flask import Flask, render_template, request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests
from requests.exceptions import HTTPError
import base64
from requests import post

app = Flask(__name__, template_folder='templates')

YT_API_KEY = 'AIzaSyBzwlWna8YoX7HqBqLoGqqwCy-9P1pDqGU'
CLIENT_ID = "599f9db771454a389913a11c7a941ec6"
CLIENT_SECRET = "3ba77fb42f454049a2dc545de4eee14a"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri='http://localhost:8888/callback',
    scope = 'playlist-modify-public'
))
user = sp.current_user()
USER_ID = user['id']

def ask_user():
    playlist_input = request.form.get('playlistInput')
    return playlist_input

def get_authenticated_service():
    youtube = build('youtube', 'v3', developerKey=YT_API_KEY)
    return youtube

def set_playlist_localizations(youtube, playlist_input):
    songs = []
    playlist_items_resource = youtube.playlistItems()
    playlist_items_request = playlist_items_resource.list(
        part='snippet',
        maxResults=50,
        playlistId=playlist_input
    )
    response = playlist_items_request.execute()
    items = response['items']
    for item in items:
        yt_title = item['snippet']['title']
        songs.append(yt_title)
    return songs

def get_token():
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    token_url = 'https://accounts.spotify.com/api/token'
    data = {'grant_type': 'client_credentials'}
    h = {'Authorization': f"Basic {base64_auth}"}
    response = requests.post(token_url, data=data, headers=h)
    token = response.json()['access_token']
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    playlist_data = {
        'name': 'Nice playlist',
        'public': True,
        'collaborative': False,
        'description': 'Playlist made with code'
    }
    
    new_playlist = sp.user_playlist_create(
        user=USER_ID,
        name='Made with Python',
        public=True,
        description='Playlist made with code'
    )
    playlist_id = new_playlist['uri']
    return playlist_id

def add_songs(songs, playlist_id):
    for song in songs:
        results = sp.search(q=song, limit=10, offset=0, type='track', market=None)
        uri = results['tracks']['items'][0]['uri']
        sp.playlist_add_items(playlist_id=playlist_id, items=[uri], position=None)
        print('Song added')

@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        playlist_input = ask_user()
        youtube = get_authenticated_service()
        songs = set_playlist_localizations(youtube, playlist_input)
        playlist_id = get_token()
        add_songs(songs, playlist_id)
        return render_template('success.html')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)