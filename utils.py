import pandas as pd
from fuzzywuzzy import fuzz
import time
from datetime import date


def get_search_results_from_query(ytdriver, query):
    """
    if artist in search results
        then if query == artist
            return all artist albums + albums + playlists
            elif query = artist + something else
                then return only albums + playlists
    else return direct albums and playlists from search results
    """
    query = query.lower()
    results = ytdriver.search(query)
    if results == []:
        # some search end up with errors, adding the token 'albums' solve this issue
        results = ytdriver.search(query + ' albums')
        if results == []:
            return {
                'albums': [],
                'playlists': []
            }
    df_search = pd.DataFrame(results)
    # first if, check if artist in df_search
    if 'artist' in df_search['resultType'].unique():
        # check if search only artist
        artists = [elt for elt in df_search[df_search['resultType'] == 'artist']['artist'].unique()]
        artist_browseId = None
        for artist in artists:
            artist_fuzz = artist.lower()
            if artist_fuzz.startswith("the "):
                artist_fuzz = artist_fuzz[4:]
            if query.startswith("the "):
                query = query[4:]
            if fuzz.ratio(query, artist_fuzz) == 100:
                artist_browseId = df_search[(df_search['resultType'] == 'artist') & (df_search['artist'] == artist)]['browseId'].max()
                break
        # get artist
        if artist_browseId:
            print('searched artist!')
            artist_details = ytdriver.get_artist(artist_browseId)
            album_list_ids = [elt['browseId'] for elt in artist_details.get('albums', {'results': []})['results']]
            # albums
            albums_details = get_all_albums_details(ytdriver, album_list_ids)
            # playlists
            playlists = [elt for elt in df_search[df_search['resultType'] == 'playlist']['browseId'].unique()]
            playlists_details = get_all_playlists_details(ytdriver, playlists)
        else:
            print('searched something else!')
            # playlists
            playlists = [elt for elt in df_search[df_search['resultType'] == 'playlist']['browseId'].unique()]
            playlists_details = get_all_playlists_details(ytdriver, playlists)
            # albums
            albums = [elt for elt in df_search[df_search['resultType'] == 'album']['browseId'].unique()]
            albums_details = get_all_albums_details(ytdriver, albums)
    else:
        print('searched something else!')
        # playlists
        playlists = [elt for elt in df_search[df_search['resultType'] == 'playlist']['browseId'].unique()]
        playlists_details = get_all_playlists_details(ytdriver, playlists)
        # albums
        albums = [elt for elt in df_search[df_search['resultType'] == 'album']['browseId'].unique()]
        albums_details = get_all_albums_details(ytdriver, albums)
    return {
        'albums': albums_details,
        'playlists': playlists_details
    }


def get_all_albums_details(ytdriver, albums_list):
    albums = []
    for album in albums_list:
        try:
            album_results = ytdriver.get_album(album)
        except KeyError:
            continue
        album_results['_id'] = album_results['playlistId']
        if not album_results['artist']:
            album_results['artist'] = [{'name': 'Various Artists'}]
        album_results['artists'] = album_results['artist']
        album_results['artist'] = album_results['artist'][0]['name']
        album_results['thumbnail'] = album_results['thumbnails'][-1]['url']
        album_results['releaseDate'] = date(album_results['releaseDate']['year'], album_results['releaseDate']['month'], album_results['releaseDate']['day']).strftime('%Y-%m-%d')
        for elt in album_results['tracks']:
            elt['_id'] = elt['videoId']
            elt['duration'] = int(int(elt['lengthMs'])/1000)
            elt['durationDisplay'] = time.strftime('%H:%M:%S', time.gmtime(elt['duration'])) if elt['duration'] > 3600 else time.strftime('%M:%S', time.gmtime(elt['duration']))
            elt['thumbnail'] = elt['thumbnails'][-1]['url']
            elt['artist'] = elt['artists']
        albums.append(album_results)
    return albums


def get_all_playlists_details(ytdriver, playlists_list):
    playlists = []
    for playlist in playlists_list:
        playlist_results = ytdriver.get_playlist(playlist)
        playlist_results['artist'] = playlist_results['author']['name']
        playlist_results['thumbnail'] = playlist_results['thumbnails'][-1]['url']
        new_tracks = []
        for elt in playlist_results['tracks']:
            if 'duration' not in elt or not elt['videoId']:
                continue
            elt['_id'] = elt['videoId']
            elt['durationDisplay'] = elt['duration']
            if len(elt['durationDisplay'].split(':')) == 3:
                elt['duration'] = int(elt['duration'].split(':')[0]) * 3600 + int(elt['duration'].split(':')[1]) * 60 + int(elt['duration'].split(':')[2])
            if len(elt['durationDisplay'].split(':')) == 2:
                elt['duration'] = int(elt['duration'].split(':')[0]) * 60 + int(elt['duration'].split(':')[1])
            elt['thumbnail'] = elt['thumbnails'][-1]['url']
            elt['artist'] = elt['artists'][0]['name']
            elt['album'] = elt['album']['name'] if elt['album'] and 'name' in elt['album'] else None
            new_tracks.append(elt)
        playlist_results['tracks'] = new_tracks
        playlist_results['_id'] = playlist_results['id']
        playlists.append(playlist_results)
    return playlists
