import time
import telebot
from telebot import types
from connectors import r, bot
from localsettings import RABBIT
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
    r.expire('active_users', 604800)
    if 'album:' in message:
        url = r.hget('user:{}:search'.format(chat_id), message)
    else:
        url = message
    songs = get_songs(url)

    with ClusterRpcProxy(RABBIT) as rpc:
        rpc.downloader.download.call_async(songs, chat_id)

def call_get_spoti_albums(message, chat_id):
    url = message
    spotisearch = SpootySearch()
    albums = spotisearch.get_albums(url)
    key = types.InlineKeyboardMarkup()
    for album in albums:
        callback = 'spotify_album:' + album['url']
        key.add(types.InlineKeyboardButton(album['name'], callback_data=callback))
    text = 'Select album:'
    bot.send_message(chat_id, text, reply_markup=key)

def call_get_spoti_songs(message, chat_id):
    timestamp = int(time.time())
    r.zadd('active_users', {chat_id: timestamp})
    r.expire('active_users', 604800)
    url = message
    spotisearch = SpootySearch()
    songs = spotisearch.get_songs(url)
    with ClusterRpcProxy(RABBIT) as rpc:
        rpc.downloader.download.call_async(songs, chat_id)