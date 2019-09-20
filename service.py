from nameko.rpc import rpc, RpcProxy
from localsettings import UPLOAD_DIR
from connectors import bot
import requests
import string
import random
import json
import os

def random_string():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(8))

class Uploader(object):
    name = "uploader"
    @rpc
    def upload(self, chat_id, order_list, tmp_dir, cover_path, artist, album):
        try:
            #upload cover
            cover = open(cover_path, 'rb')
            bot.send_photo(chat_id, cover, caption='{} - {}'.format(artist, album))
            for info in order_list:
                file = info[1]
                name = info[2]
                audio = open(file, 'rb')
                bot.send_audio(chat_id, audio, performer=artist, title=name)
                os.remove(file)
            os.remove(cover_path)
            os.rmdir('{}/{}'.format(UPLOAD_DIR, tmp_dir))
        except Exception as e:
            return e

class Downloader(object):
    name = "downloader"
    uploader = RpcProxy('uploader')
    @rpc
    def download(self, obj, chat_id):
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
                    r = requests.get(url)
                    with open('{}/{}/{}.mp3'.format(UPLOAD_DIR, tmp_dir, tmp_song), 'wb') as f:
                        f.write(r.content)
                    order_list.append((num, '{}/{}/{}.mp3'.format(UPLOAD_DIR, tmp_dir, tmp_song), name))
            #call uploader
            self.uploader.upload.call_async(chat_id, order_list, tmp_dir, cover_path, artist, album)
        except Exception as e:
            return e