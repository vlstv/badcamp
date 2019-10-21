import time
import telebot
from telebot import types
from connectors import r, bot
from localsettings import RABBIT, STORAGE_GROUP_ID
from parser import get_albums, get_songs, search
from nameko.standalone.rpc import ClusterRpcProxy
from service import random_string
from spotisearch import SpootySearch
from models import Albums, Songs

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
    text = '👾 Select album:'
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
    text = '👾 Select album:'
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
    try:
        album_id = Albums.query.filter_by(artist=artist, name=album).first().id
        song_id = Songs.query.filter_by(album_id=album_id, name=song).first().id
        with ClusterRpcProxy(RABBIT) as rpc:
            rpc.downloader.blame.call_async(chat_id, album_id, song_id, url, song, artist)
    except Exception as e:
        bot.send_message(chat_id, e)

def badcamp_search(chat_id, query):
    results = search(query)
    key = types.InlineKeyboardMarkup()
    for result in results:
        if len(result['url']) <= 64:
            callback = result['url']
        else:
            search_key = 'user:{}:search'.format(chat_id)
            if result['type'] == 'album':
                callback = 'album:{}'.format(random_string())
                r.hset(search_key, callback, result['url'])
                r.expire(search_key, 240)
            elif result['type'] == 'band':
                callback = 'band:{}'.format(random_string())
                r.hset(search_key, callback, result['url'])
                r.expire(search_key, 240)
        if result['type'] == 'album':
            key.add(types.InlineKeyboardButton('{} - {} ({})'.format(result['band'], result['album'], result['type']), callback_data=callback))
        if result['type'] == 'band':
            key.add(types.InlineKeyboardButton('{} ({})'.format(result['band'], result['type']), callback_data=callback))
    text = '👾 Select resource:'
    bot.send_message(chat_id, text, reply_markup=key)

def spoti_search(chat_id, query):
    spootisearch = SpootySearch()
    results = spootisearch.get_artists(query)
    key = types.InlineKeyboardMarkup()
    for result in results:
        callback = 'spotify_artist:' + result['url']
        key.add(types.InlineKeyboardButton('{} ({})'.format(result['band'], result['type']), callback_data=callback))
    text = '👾 Select resource:'
    bot.send_message(chat_id, text, reply_markup=key)