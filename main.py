from flask import Flask, request
from flask_cors import CORS, cross_origin

from ytmusicapi import YTMusic
from utils import get_search_results_from_query
import os
from exceptions import TooManyRequests

from convert_playlist import Spotify, YTMusicTransfer

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/search/yt', methods=['POST'])
@cross_origin()
def search_yt_music():
    ytmusic = YTMusic('headers_auth.json')
    query = request.json.get('query')
    try:
        results = get_search_results_from_query(ytmusic, query)
        return results
    except TooManyRequests:
        return {'error': 'Too many requests.'}


@app.route('/setup/yt', methods=['POST'])
@cross_origin()
def setup_yt_music():
    headers = request.json.get('headers')
    try:
        os.remove('headers_auth.json')
    except FileNotFoundError:
        pass
    YTMusic.setup(filepath='headers_auth.json', headers_raw=headers)
    return {'result': 'New headers_auth.json set'}


@app.route('/convert/spotify', methods=['POST'])
@cross_origin()
def convert_playlist_to_youtube():
    playlist_url = request.json.get('url')
    try:
        playlist = Spotify().getSpotifyPlaylist(playlist_url)
        results = YTMusicTransfer().search_songs(playlist['tracks'])
        return {'playlist': results}
    except TooManyRequests:
        return {'error': 'Too many requests.'}


@app.route('/health')
@cross_origin()
def health():
    return 'Hello World'
