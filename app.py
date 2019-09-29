from localsettings import TOKEN, WEBHOOK_URL
from parser import get_albums, get_songs, search
from helpers import call_get_albums, call_get_songs, call_get_spoti_albums
from service import random_string
from connectors import r, bot
from flask import Flask
import telebot
from telebot import types
import flask
import json
import re
from spotisearch import SpootySearch

app = Flask(__name__)

@app.route('/', methods=['POST','GET'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

@bot.message_handler(commands=['search'])
def handle_search(message):
    try:
        arg = message.text.replace('/search ', '')
        results = search(arg)
        key = types.InlineKeyboardMarkup()
        for result in results:
            if len(result['url']) <= 64:
                callback = result['url']
            else:
                search_key = 'user:{}:search'.format(message.chat.id)
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
        text = 'Select resource:'
        bot.send_message(message.chat.id, text, reply_markup=key)
    except Exception as e:
        bot.send_message(message.chat.id, e)

#spotiserch test
@bot.message_handler(commands=['spoti'])
def handle_spoti(message):
    try:
        arg = message.text.replace('/spoti ', '')
        spootisearch = SpootySearch()
        results = spootisearch.get_artists(arg)
        key = types.InlineKeyboardMarkup()
        for result in results:
            callback = 'spotify_artist:' + result['url']
            key.add(types.InlineKeyboardButton('{} ({})'.format(result['band'], result['type']), callback_data=callback))
        text = 'Select resource:'
        bot.send_message(message.chat.id, text, reply_markup=key)
    except Exception as e:
        bot.send_message(message.chat.id, e)

@bot.message_handler(content_types=['text'])
def handle_start(message):
    try:
        if 'album' in message.text or 'track' in message.text:
            call_get_songs(message.text, message.chat.id)
        elif re.match(r'https:\/\/*.*\.bandcamp\.com\/', message.text):
            call_get_albums(message.text[:-1], message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, e)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if 'album' in call.data:
                call_get_songs(call.data, call.message.chat.id)
            elif 'spotify_artist' in call.data:
                a = call.data.split(':')
                call_get_spoti_albums(a[1], call.message.chat.id)
            elif 'spotify_album' in call.data:
                a = call.data.split(':')
                call_get_spoti_albums(a[1], call.message.chat.id)
            else:
                call_get_albums(call.data, call.message.chat.id)
    except Exception as e:
        bot.send_message(call.message.chat.id, e)


bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    app.run()
