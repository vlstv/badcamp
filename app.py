from localsettings import TOKEN, WEBHOOK_URL
from helpers import call_get_albums, call_get_songs, call_get_spoti_albums, call_get_spoti_songs, blame, badcamp_search, spoti_search
from service import random_string
from connectors import r, bot, app
from flask import Flask
import telebot
from telebot import types
import flask
import json
import re
from spotisearch import SpootySearch
import logging

log = logging.getLogger(__name__)

@app.route('/', methods=['POST','GET'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

@bot.message_handler(commands=['blame'])
def blame_song(message):
    try:
        if message.text == '/blame':
            bot.send_message(message.chat.id, '⚠️ Use /blame command to report for a wrong track downloaded from youtube. Please follow this syntax:\n \
                        /blame Artist\nAlbum\nSong\nURL from youtube', parse_mode='markdown')
        else:
            args = message.text.replace('/blame ', '')
            args = args.split('\n')
            artist = args[0]
            album = args[1]
            song = args[2]
            url = args[3]
            blame(message.chat.id, artist, album, song, url)
    except Exception as e:
        bot.send_message(message.chat.id, e)
        log.error(e)

@bot.message_handler(commands=['search'])
def handle_test(message):
    try:
        if message.text == '/search':
            bot.send_message(message.chat.id, '⚠️ What are you searching for?\n*Format*: _/search [artist/album]_', parse_mode='markdown')
        else:
            query = message.text.replace('/search ', '')
            key = types.InlineKeyboardMarkup()
            key.add(types.InlineKeyboardButton('Search and download from bandcamp', callback_data='bandcamp_search:{}'.format(query)))
            key.add(types.InlineKeyboardButton('Search in spotify, download from youtube', callback_data='spoti_search:{}'.format(query)))
            bot.send_message(message.chat.id, '👾 Select search method:', reply_markup=key)
    except Exception as e:
        bot.send_message(message.chat.id, e)
        log.error(e)

@bot.message_handler(content_types=['text'])
def handle_start(message):
    try:
        if 'album' in message.text or 'track' in message.text:
            call_get_songs(message.text, message.chat.id)
        elif re.match(r'https:\/\/*.*\.bandcamp\.com\/', message.text):
            call_get_albums(message.text[:-1], message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, e)
        log.error(e)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            #Remove markup to prevent doubleclicks 
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            if 'album' in call.data:
                bot.send_message(call.message.chat.id, '👾 Your download has been started,\
                                            it can take several minutes depending on server load. Please be patient')
                call_get_songs(call.data, call.message.chat.id)
            elif 'spotify_artist' in call.data:
                call_get_spoti_albums(call.data.split(':')[1], call.message.chat.id)
            elif 'spotify_al' in call.data:
                bot.send_message(call.message.chat.id, '👾 Your download has been started,\
                                            it can take several minutes depending on server load. Please be patient')
                call_get_spoti_songs(call.data.split(':')[1], call.message.chat.id)
            elif 'bandcamp_search' in call.data:
                badcamp_search(call.message.chat.id, call.data.split(':')[1])
            elif 'spoti_search' in call.data:
                spoti_search(call.message.chat.id, call.data.split(':')[1])
            else:
                call_get_albums(call.data, call.message.chat.id)

    except Exception as e:
        bot.send_message(call.message.chat.id, e)
        log.error(e)

bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    app.run()