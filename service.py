from nameko.rpc import rpc, RpcProxy
from localsettings import UPLOAD_DIR, STORAGE_GROUP_ID, LOG_LOCATION 
from connectors import bot, db
from models import Songs, Albums
import requests
import string
import random
import json
import os
import youtube_dl
import logging

logging.basicConfig(filename=LOG_LOCATION, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger('service')

def random_string():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(8))

class Uploader(object):
    name = "uploader"
    @rpc
    def upload(self, chat_id, order_list, tmp_dir, cover_path, artist, album, cover_url, single_song):
        try:
            #save album in db
            if single_song == False:
                a = Albums(name=album,cover=cover_url,artist=artist)
                db.session.add(a)
                db.session.commit()
            album_id = a.id
            album_messages = []
            #upload cover to storage group
            cover = open(cover_path, 'rb')
            bot.send_photo(STORAGE_GROUP_ID, cover, caption='{} - {}'.format(artist, album), disable_notification=True)
            for info in order_list:
                file = info[1]
                name = info[2]
                try:
                    audio = open(file, 'rb')
                    message = bot.send_audio(STORAGE_GROUP_ID, audio, performer=artist, title=name, disable_notification=True)
                    album_messages.append([name,message.message_id])
                except Exception as e:
                    bot.send_message(chat_id, '⚠️ Error, skipping track - {}. Reason:\n{}'.format(name, e))
                os.remove(file)
            #upload cover to chat
            cover = open(cover_path, 'rb')
            bot.send_photo(chat_id, cover, caption='{} - {}'.format(artist, album), disable_notification=True)
            os.remove(cover_path)
            os.rmdir('{}/{}'.format(UPLOAD_DIR, tmp_dir))
            #forward from storage group
            order_id = 0
            for album_message in album_messages:
                name = album_message[0]
                message_id = album_message[1]
                bot.forward_message(chat_id, STORAGE_GROUP_ID, message_id)
                #save in db
                if single_song == False:
                    s = Songs(id=message_id,name=name,album_id=album_id, order_id=order_id)
                    db.session.add(s)
                    order_id += 1
            if single_song == False:
                db.session.commit()
        except Exception as e:
            bot.send_message(chat_id, '⚠️ Oooops, an error occurred during album upload, we are on it')
            log.error(e)

    @rpc
    def upload_blame(self, chat_id, tmp_dir, song_path, artist, name, album_id, song_id):
        try:
            audio = open(song_path, 'rb')
            message = bot.send_audio(STORAGE_GROUP_ID, audio, performer=artist, title=name, disable_notification=True)
            new_message_id = message.message_id
            os.remove(song_path)
            os.rmdir('{}/{}'.format(UPLOAD_DIR, tmp_dir))
            d = Songs.query.filter_by(id=song_id).first()
            d.id = new_message_id
            db.session.commit()
            bot.send_message(chat_id, 'Done! You can now re-download the whole album')
        except Exception as e:
            bot.send_message(chat_id, '⚠️ Oooops, an error occurred, we are on it')
            log.error(e)

class Downloader(object):
    name = "downloader"
    uploader = RpcProxy('uploader')
    @rpc
    def download(self, obj, chat_id, single_song=False):
        try:
            artist = obj["artist"]
            album = obj["album"]
            songs = obj["songs"]
            cover = obj["cover"]
            tmp_dir =  random_string()
            os.mkdir('{}/{}'.format(UPLOAD_DIR,tmp_dir))
            #downloadcover
            r = requests.get(cover)
            cover_path = '{}/{}/{}.jpeg'.format(UPLOAD_DIR, tmp_dir, random_string())
            with open(cover_path, 'wb') as f:
                f.write(r.content)
            #download songs
            order_list = []
            for song in songs:
                for num, info in song.items():
                    name = info[0]
                    url = info[1]
                    tmp_song = random_string()
                    if 'youtube' in url:
                        order_element = download_youtube(num, tmp_dir, tmp_song, url, name)
                    else:
                        order_element = download_badcamp(num, tmp_dir, tmp_song, url, name)
                    order_list.append(order_element)
            #call uploader
            self.uploader.upload.call_async(chat_id, order_list, tmp_dir, cover_path, artist, album, cover, single_song)
        except Exception as e:
            bot.send_message(chat_id, '⚠️ Oooops, an error occurred during album download, we are on it')
            log.error(e)

    @rpc
    def blame(self, chat_id, album_id, song_id, url, name, artist):
        try:
            tmp_dir =  random_string()
            tmp_song =  random_string()
            os.mkdir('{}/{}'.format(UPLOAD_DIR,tmp_dir))
            if 'youtube' in url:
                order_element = download_youtube(0, tmp_dir, tmp_song, url, name)
            else:
                order_element = download_badcamp(0, tmp_dir, tmp_song, url, name)
            song_path = order_element[1]
            self.uploader.upload_blame.call_async(chat_id, tmp_dir, song_path, artist, name, album_id, song_id)
        except Exception as e:
            bot.send_message(chat_id, '⚠️ Oooops, an error occurred, we are on it')
            log.error(e)

def download_badcamp(num, tmp_dir, tmp_song, url, name):
    r = requests.get(url)
    with open('{}/{}/{}.mp3'.format(UPLOAD_DIR, tmp_dir, tmp_song), 'wb') as f:
        f.write(r.content)
    return (num, '{}/{}/{}.mp3'.format(UPLOAD_DIR, tmp_dir, tmp_song), name)

def download_youtube(num, tmp_dir, tmp_song, url, name):
    download_options = {
        'format': 'bestaudio/best',
        'outtmpl': '{}/{}/{}'.format(UPLOAD_DIR, tmp_dir, tmp_song) + '.%(ext)s',
        'nocheckcertificate': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            }]
        }

    with youtube_dl.YoutubeDL(download_options) as dl:
        dl.download([url])
    return (num, '{}/{}/{}.mp3'.format(UPLOAD_DIR, tmp_dir, tmp_song), name)

def in_db(artist, album, chat_id):
    album = Albums.query.filter_by(artist=artist, name=album).first()
    if album != None:
        #forward downloaded messages
        songs = Songs.query.filter_by(album_id=album.id).order_by(Songs.order_id)
        #send cover
        bot.send_photo(chat_id, album.cover, caption='{} - {}'.format(album.artist, album.name), disable_notification=True)
        for song in songs:
            bot.forward_message(chat_id, STORAGE_GROUP_ID, song.id)
    else:
        return False