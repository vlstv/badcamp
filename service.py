from nameko.rpc import rpc, RpcProxy
from localsettings import UPLOAD_DIR
from connectors import bot
import mutagen
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
import requests
import string
import random
import json
import os

def mutate(file, artist, name):
    try:
        try:
            audiofile = EasyID3(file)
            audiofile['artist'] = artist
            audiofile['title'] = name
            audiofile.save()
        except mutagen.id3.ID3NoHeaderError:
            audiofile = mutagen.File(file, easy=True)
            audiofile.add_tags()
            audiofile['artist'] = artist
            audiofile['title'] = name
            audiofile.save()
    except Exception as e:
        return e

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
                mutate(file, artist, name)
                audio = open(file, 'rb')
                bot.send_audio(chat_id, audio)
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
            tmp_dir =  ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))
            os.mkdir('{}/{}'.format(UPLOAD_DIR,tmp_dir))
            #downloadcover
            r = requests.get(cover)
            cover_path = '{}/{}/{}.jpeg'.format(UPLOAD_DIR, tmp_dir, album)
            with open(cover_path, 'wb') as f:
                f.write(r.content)
            #download songs
            order_list = []
            for song in songs:
                for num, info in song.iteritems():
                    name = info[0]
                    url = info[1]
                    r = requests.get(url)
                    with open('{}/{}/{}.mp3'.format(UPLOAD_DIR, tmp_dir, name), 'wb') as f:
                        f.write(r.content)
                    order_list.append((num, '{}/{}/{}.mp3'.format(UPLOAD_DIR, tmp_dir, name), name))
            #call uploader
            self.uploader.upload.call_async(chat_id, order_list, tmp_dir, cover_path, artist, album)
        except Exception as e:
            return e