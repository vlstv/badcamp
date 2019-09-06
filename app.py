from nameko.standalone.rpc import ClusterRpcProxy
from localsettings import RABBIT, TOKEN, WEBHOOK_URL
from parser import get_albums, get_songs
from connectors import r, bot
from flask import Flask
import telebot
import flask
import json
import re

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

@bot.message_handler(content_types=['text'])
def handle_start(message):

    album_key = 'user:{}:albums'.format(message.chat.id)

    try:
        if re.match(r'https:\/\/*.*\.bandcamp\.com\/', message.text) and 'track' not in message.text:
            albums = get_albums(message.text)
            r.set(album_key, json.dumps(albums), 300)
            album_list = ''
            for album in albums:
                text = '{} - {}\n'.format(str(album['id']), album['name'])
                album_list += text
            bot.send_message(message.chat.id, album_list)
        elif message.text.isdigit() == True:
            albums = json.loads(r.get(album_key))
            for album in albums:
                if album["id"] == int(message.text):
                    songs = get_songs(album["url"])
                    with ClusterRpcProxy(RABBIT) as rpc:
                        rpc.downloader.download.call_async(songs, message.chat.id)
        elif 'track' in message.text:
            song = get_songs(message.text)
            with ClusterRpcProxy(RABBIT) as rpc:
                rpc.downloader.download.call_async(song, message.chat.id)
        elif 'album' in message.text:
            song = get_songs(message.text)
            with ClusterRpcProxy(RABBIT) as rpc:
                rpc.downloader.download.call_async(song, message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, e)

bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    app.run()