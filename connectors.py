from localsettings import REDIS_HOST, REDIS_PORT, TOKEN, DB_*
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
  database=DB_NAME
)

cursor = badcamp_db.cursor()