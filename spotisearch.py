import json
from lxml import html
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import youtube
import requests
from service import random_string
import os
from localsettings import *

class SpootySearch():
    def __init__(self):
        self.client_credentials_manager = SpotifyClientCredentials(SPOTIFY_ID, SPOTIFY_SECRET)
        self.spotify = spotipy.Spotify(client_credentials_manager=self.client_credentials_manager)
        self.youtube_api = youtube.API(client_id=YOUTUBE_ID, client_secret=YOUTUBE_SECRET, api_key=YOUTUBE_KEY)

    def get_songs(self, id):
        results = self.spotify.album(id)
        artist = results["artists"][0]["name"]
        album = results["name"]
        cover = results["images"][0]["url"]
        songs = results["tracks"]["items"]
        id = 0
        songs_list = []
        for song in songs:
            query = artist + song["name"]
            try:
                url = self.search_youtube_parse(query)
            except:
                url = self.search_youtube_api(query)
            songs_list.append({id:[song["name"], url]})
            id += 1 
        return {'artist': artist, 'album': album, 'cover': cover, "songs": songs_list}

    def get_albums(self, id):
        results = self.spotify.artist_albums(id)
        albums = results["items"]
        result_list = []
        for album in albums:
            resource_info = {}
            resource_info['name'] = album['name']
            resource_info['url'] = album['id']
            result_list.append(resource_info)
        result_list = { each['name'] : each for each in result_list}.values()
        return result_list

    def get_artists(self, q):
        results = self.spotify.search(q, limit=5, type='artist')
        artists = results["artists"]["items"]
        result_list = []
        for artist in artists:
            resource_info = {}
            resource_info['type'] = 'band'
            resource_info['band'] = artist['name']
            resource_info['url'] = artist['id']
            result_list.append(resource_info)
        return result_list

    def search_youtube_api(self, songName):
        url = "https://www.youtube.com/results?search_query=" + songName
        response = requests.get(url)
        tree = html.fromstring(response.text)
        uri = tree.xpath("//a[contains(@class, 'yt-uix-tile-link')]/@href")[0]
        return 'https://www.youtube.com' + uri

    def search_youtube_parse(self, songName):
        video = self.youtube_api.get('search', q=songName, maxResults=1, type='video', order='relevance')
        return "https://www.youtube.com/watch?v="+video["items"][0]["id"]["videoId"]


