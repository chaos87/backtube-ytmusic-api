
from ytmusicapi import YTMusic
from datetime import datetime
import os
import re
import argparse
import difflib
from collections import OrderedDict
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import html

class Spotify:
    def __init__(self):
        conf = {
            'client_id': os.environ['SPOTIFY_CLIENT_ID'],
            'client_secret': os.environ['SPOTIFY_CLIENT_SECRET']
        }
        client_credentials_manager = SpotifyClientCredentials(client_id=conf['client_id'], client_secret=conf['client_secret'])
        self.api = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def build_results(self, tracks):
        results = []
        for track in tracks['items']:
            if track['track'] is not None:
                results.append({
                    'artist': ' '.join([artist['name'] for artist in track['track']['artists']]),
                    'name': track['track']['name'],
                    'album': track['track']['album']['name'],
                    'duration': track['track']['duration_ms']/1000
                })

        return results

    def getSpotifyPlaylist(self, url):
        url_parts = url.split('/')
        try:
            playlistId = url_parts[4].split('?')[0]
        except:
            raise Exception('Bad playlist url: ' + url)
        if len(playlistId) != 22:
            raise Exception('Bad playlist id: ' + playlistId)

        results = self.api.playlist(playlistId)
        name = results['name']
        tracks = self.build_results(results['tracks'])

        count = 1
        more = len(results['tracks']['items']) == 100
        while more:
            items = self.api.playlist_tracks(playlistId, offset = count * 100, limit=100)
            print('requested from ' + str(count * 100))
            tracks += self.build_results(items)
            more = len(items["items"]) == 100
            count = count + 1

        return {'tracks': tracks, 'name': name, 'description': html.unescape(results['description'])}

    def getUserPlaylists(self, user):
        pl = self.api.user_playlists(user)['items']
        count = 1
        more = len(pl) == 50
        while more:
            results = self.api.user_playlists(user, offset=count * 50)['items']
            pl.extend(results)
            more = len(results) == 50
            count = count + 1

        return [p for p in pl if p['owner']['display_name'] == user and p['tracks']['total'] > 0]


class YTMusicTransfer:
    def __init__(self):
        self.api = YTMusic()

    def create_playlist(self, name, info, privacy="PRIVATE", tracks=None):
        return self.api.create_playlist(name, info, privacy, video_ids=tracks)

    def get_best_fit_song(self, results, song):
        match_score = {}
        title_score = {}
        for res in results:
            if res['resultType'] not in ['song', 'video']:
                continue

            durationMatch = None
            if res['duration']:
                durationItems = res['duration'].split(':')
                duration = int(durationItems[0]) * 60 + int(durationItems[1])
                durationMatch = 1 - abs(duration - song['duration']) * 2 / song['duration']

            title = res['title']
            # for videos,
            if res['resultType'] == 'video':
                titleSplit = title.split('-')
                if len(titleSplit) == 2:
                    title = titleSplit[1]

            artists = ' '.join([a['name'] for a in res['artists']])

            title_score[res['videoId']] = difflib.SequenceMatcher(a=title.lower(), b=song['name'].lower()).ratio()
            scores = [title_score[res['videoId']],
                      difflib.SequenceMatcher(a=artists.lower(), b=song['artist'].lower()).ratio()]
            if durationMatch:
                scores.append(durationMatch * 5)

            #add album for songs only
            if res['resultType'] == 'song' and res['album'] is not None:
                scores.append(difflib.SequenceMatcher(a=res['album']['name'].lower(), b=song['album'].lower()).ratio())

            match_score[res['videoId']] = sum(scores) / (len(scores) + 1) * max(1, int(res['resultType'] == 'song') * 1.5)

        if len(match_score) == 0:
            return None

        #don't return songs with titles <45% match
        max_score = max(match_score, key=match_score.get)
        return [el for el in results if el['resultType'] in ['song', 'video'] and el['videoId'] == max_score][0]

    def search_songs(self, tracks):
        videos = []
        songs = list(tracks)
        notFound = list()
        for i, song in enumerate(songs):
            query = song['artist'] + ' ' + song['name']
            query = query.replace(" &", "")
            try:
                result = self.api.search(query)
            except:
                print(f'Fail for {song["artist"]} - {song["name"]}')
            if len(result) == 0:
                notFound.append(query)
            else:
                targetSong = self.get_best_fit_song(result, song)
                if targetSong is None:
                    notFound.append(query)
                else:
                    video = self.format_song(targetSong)
                    videos.append(video)

            if i > 0 and i % 10 == 0:
                print(str(i) + ' searched')
        print(notFound)

        return videos

    def format_song(self, video):
        video['_id'] = video['videoId']
        video['durationDisplay'] = video['duration']
        if len(video['durationDisplay'].split(':')) == 3:
            video['duration'] = int(video['duration'].split(':')[0]) * 3600 + int(video['duration'].split(':')[1]) * 60 + int(video['duration'].split(':')[2])
        if len(video['durationDisplay'].split(':')) == 2:
            video['duration'] = int(video['duration'].split(':')[0]) * 60 + int(video['duration'].split(':')[1])
        video['thumbnail'] = video['thumbnails'][-1]['url']
        video['artist'] = video['artists'][0]['name']
        video['album'] = video['album']['name'] if 'album' in video and 'name' in video['album'] else None
        return video

    def add_playlist_items(self, playlistId, videoIds):
        videoIds = OrderedDict.fromkeys(videoIds)
        self.api.add_playlist_items(playlistId, videoIds)

    def get_playlist_id(self, name):
        pl = self.api.get_library_playlists(10000)
        try:
            playlist = next(x for x in pl if x['title'].find(name) != -1)['playlistId']
            return playlist
        except:
            raise Exception("Playlist title not found in playlists")

    def remove_songs(self, playlistId):
        items = self.api.get_playlist(playlistId, 10000)['tracks']
        if len(items) > 0:
            self.api.remove_playlist_items(playlistId, items)

    def remove_playlists(self, pattern):
        playlists = self.api.get_library_playlists(10000)
        p = re.compile("{0}".format(pattern))
        matches = [pl for pl in playlists if p.match(pl['title'])]
        print("The following playlists will be removed:")
        print("\n".join([pl['title'] for pl in matches]))
        print("Please confirm (y/n):")

        choice = input().lower()
        if choice[:1] == 'y':
            [self.api.delete_playlist(pl['playlistId']) for pl in matches]
            print(str(len(matches)) + " playlists deleted.")
        else:
            print("Aborted. No playlists were deleted.")
