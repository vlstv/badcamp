from localsettings import REDIS_HOST, REDIS_PORT, TOKEN
from localsettings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
import mysql.connector
import telebot
import redis

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT)

bot = telebot.TeleBot(TOKEN, threaded=False)

badcamp_db = mysql.connector.connect(
  host=DB_HOST,
  user=DB_USER,
  passwd=DB_PASSWORD,
  database=DB_NAME,
  port=DB_PORT
)

cursor = badcamp_db.cursor()