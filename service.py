from nameko.rpc import rpc, RpcProxy
from localsettings import UPLOAD_DIR, STORAGE_GROUP_ID
from connectors import bot, cursor, badcamp_db
import requests
import string
import random
import json
import os
import youtube_dl

def random_string():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(8))

class Uploader(object):
    name = "uploader"
    @rpc
    def upload(self, chat_id, order_list, tmp_dir, cover_path, artist, album, cover_url):
        try:
            #save album in db
            cursor.execute('INSERT INTO albums (name, cover, artist) VALUES (%s, %s, %s)', (album, cover_url, artist))
            badcamp_db.commit()
            album_id = cursor.lastrowid
            album_messages = []
            #upload cover to storage group
            cover = open(cover_path, 'rb')
            bot.send_photo(STORAGE_GROUP_ID, cover, caption='{} - {}'.format(artist, album), disable_notification=True)
            for info in order_list:
                file = info[1]
                name = info[2]
                audio = open(file, 'rb')
                message = bot.send_audio(STORAGE_GROUP_ID, audio, performer=artist, title=name, disable_notification=True)
                album_messages.append([name,message.message_id])
                os.remove(file)
            #upload cover to chat
            cover = open(cover_path, 'rb')
            bot.send_photo(chat_id, cover, caption='{} - {}'.format(artist, album), disable_notification=True)
            os.remove(cover_path)
            os.rmdir('{}/{}'.format(UPLOAD_DIR, tmp_dir))
            #forward from storage group
            for album_message in album_messages:
                name = album_message[0]
                message_id = album_message[1]
                bot.forward_message(chat_id, STORAGE_GROUP_ID, message_id)
                #save in db
                cursor.execute('INSERT INTO songs (id, name, album_id) VALUES (%s, %s, %s)', (message_id, name, album_id))
                badcamp_db.commit()
        except Exception as e:
            return e
    @rpc
    def upload_blame(self, chat_id, tmp_dir, song_path, artist, name, album_id, song_id):
        try:
            audio = open(song_path, 'rb')
            print(song_path)
            message = bot.send_audio(STORAGE_GROUP_ID, audio, performer=artist, title=name, disable_notification=True)
            new_message_id = message.message_id
            os.remove(song_path)
            os.rmdir('{}/{}'.format(UPLOAD_DIR, tmp_dir))
            #insert new
            cursor.execute('INSERT INTO songs (id, name, album_id) VALUES (%s, %s, %s)', (new_message_id, name, album_id))
            badcamp_db.commit()
            #delete old
            cursor.execute('Delete from songs where id={}'.format(song_id))
            badcamp_db.commit()
            bot.send_message(chat_id, 'Done! You can now re-download the whole album')
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
            #check if already in db
            if in_db(artist, album, chat_id) == False:
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
                self.uploader.upload.call_async(chat_id, order_list, tmp_dir, cover_path, artist, album, cover)
        except Exception as e:
            print(e)
            return e
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
            return e


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
    cursor.execute('SELECT * FROM albums where name=%s and artist=%s', (album, artist))
    result = cursor.fetchall()
    if len(result) != 0:
        #forward downloaded messages
        album_id = result[0][0]
        album = result[0][1]
        cover_url = result[0][2]
        artist = result[0][3]
        cursor.execute('SELECT id FROM songs where album_id=%s', (album_id,))
        songs_ids = cursor.fetchall()
        #send cover
        bot.send_photo(chat_id, cover_url, caption='{} - {}'.format(artist, album), disable_notification=True)
        for song_id in songs_ids:
            bot.forward_message(chat_id, STORAGE_GROUP_ID, song_id[0])
    else:
        return False