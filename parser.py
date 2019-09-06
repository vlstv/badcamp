import requests
import re
import json
from lxml import html

def get_meta(response):
    tree = html.fromstring(response.content)
    cover = tree.xpath('//img[@itemprop="image"]/@src')[0]
    meta = tree.xpath('//meta[@name="title"]/@content')[0]
    meta = meta.split(', by ')
    return {'artist': meta[1], 'album': meta[0], 'cover': cover}

def get_song_list(response):
    response = response.text
    songs  = re.findall('trackinfo:[^]]*]', response)[0].replace('trackinfo:', '')
    songs = json.loads(songs)
    song_list = []
    for song in songs:
        try:
            song_list.append({song["track_num"]: [song["title"], song["file"]["mp3-128"]]})
        except:
            pass
    return song_list

def get_songs(url):
    response = requests.get(url)
    info = get_meta(response)
    song_list = get_song_list(response)
    if len(song_list) > 0:
        info.update({'songs': song_list})
        return info
    else:
        return False

def get_albums(url):
    response = requests.get(url)
    albums_list = re.findall('\"(\/album\/[^"]*)', response.text)
    albums_list = list(dict.fromkeys(albums_list))
    id = 1
    albums = []
    for album in albums_list:
        tree = html.fromstring(response.content)
        try:
            album_name = tree.xpath('//div[@class="trackTitle"]//a[@href="'+ album +'"]/text()')[0]
        except:
            album_name = tree.xpath('//a[@href="'+ album +'"]//p[@class="title"]/text()')[0]
            album_name = re.findall('(?:[^\\n\\ ]+)(?:[^\n]+)', album_name)[0]
        albums.append({'id': id, 'name': album_name, 'url': url[:-1]+ album})
        id+=1
    return albums