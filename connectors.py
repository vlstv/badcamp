from localsettings import REDIS_HOST, REDIS_PORT, TOKEN, LOG_LOCATION
from localsettings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
import mysql.connector
import telebot
import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT)

bot = telebot.TeleBot(TOKEN, threaded=False)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}?host={}?port={}'.format(DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_HOST, DB_PORT)
db = SQLAlchemy(app)

logging.basicConfig(filename=LOG_LOCATION, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')