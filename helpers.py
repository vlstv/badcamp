import time
import telebot
from telebot import types
from connectors import r, bot
from localsettings import RABBIT
from parser import get_albums, get_songs
from nameko.standalone.rpc import ClusterRpcProxy

def call_get_albums(message, chat_id):
    if message == 'band':
        url = r.hget('user:{}:search', 'band')
    else:
        url = message
    albums = get_albums(url)
    key = types.InlineKeyboardMarkup()
    for album in albums:
        if len(album['url']) <= 64:
            callback = album['url']
        else:
            search_key = 'user:{}:search'.format(chat_id)
            r.hset(search_key, 'album', album['url'])
            r.expire(search_key, 120)
            callback = 'album'
        key.add(types.InlineKeyboardButton(album['name'], callback_data=callback))
    text = 'Select album:'
    bot.send_message(chat_id, text, reply_markup=key)

def call_get_songs(message, chat_id):
    #set user as active
    timestamp = int(time.time())
    r.zadd('active_users', {chat_id: timestamp})
    r.expire('active_users', 604800)
    if message == 'album':
        url = r.hget('user:{}:search'.format(chat_id), 'album')
    else:
        url = message
    songs = get_songs(url)

    with ClusterRpcProxy(RABBIT) as rpc:
        rpc.downloader.download.call_async(songs, chat_id)
