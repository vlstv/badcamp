import time
import telebot
from telebot import types
from connectors import r, bot, cursor, badcamp_db
from localsettings import RABBIT, STORAGE_GROUP_ID
from parser import get_albums, get_songs
from nameko.standalone.rpc import ClusterRpcProxy
from service import random_string
from spotisearch import SpootySearch

def call_get_albums(message, chat_id):
    if 'band:' in message:
        url = r.hget('user:{}:search', message)
    else:
        url = message
    albums = get_albums(url)
    key = types.InlineKeyboardMarkup()
    for album in albums:
        if len(album['url']) <= 64:
            callback = album['url']
        else:
            search_key = 'user:{}:search'.format(chat_id)
            callback = 'album:{}'.format(random_string())
            r.hset(search_key, callback, album['url'])
            r.expire(search_key, 240)
        key.add(types.InlineKeyboardButton(album['name'], callback_data=callback))
    text = 'Select album:'
    bot.send_message(chat_id, text, reply_markup=key)

def call_get_songs(message, chat_id):
    #set user as active
    timestamp = int(time.time())
    r.zadd('active_users', {chat_id: timestamp})
    if 'album:' in message:
        url = r.hget('user:{}:search'.format(chat_id), message)
    else:
        url = message
    songs = get_songs(url, chat_id)

    with ClusterRpcProxy(RABBIT) as rpc:
        rpc.downloader.download.call_async(songs, chat_id)

def call_get_spoti_albums(message, chat_id):
    url = message
    spotisearch = SpootySearch()
    albums = spotisearch.get_albums(url)
    key = types.InlineKeyboardMarkup()
    for album in albums:
        callback = 'spotify_al:' + album['url']
        key.add(types.InlineKeyboardButton(album['name'], callback_data=callback))
    text = 'Select album:'
    bot.send_message(chat_id, text, reply_markup=key)

def call_get_spoti_songs(message, chat_id):
    timestamp = int(time.time())
    r.zadd('active_users', {chat_id: timestamp})
    url = message
    spotisearch = SpootySearch()
    songs = spotisearch.get_songs(url, chat_id)
    with ClusterRpcProxy(RABBIT) as rpc:
        rpc.downloader.download.call_async(songs, chat_id)

def blame(chat_id, artist, album, song, url):
    cursor = badcamp_db.cursor()
    cursor.execute('select songs.id, albums.id from songs , albums WHERE albums.name=%s and albums.artist=%s and \
        songs.album_id = albums.id and songs.name=%s', (album, artist, song))
    result = cursor.fetchall()
    cursor.close()
    song_id = result[0][0]
    album_id = result[0][1]
    with ClusterRpcProxy(RABBIT) as rpc:
        rpc.downloader.blame.call_async(chat_id, album_id, song_id, url, song, artist)