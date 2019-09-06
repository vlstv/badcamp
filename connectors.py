from localsettings import REDIS_HOST, REDIS_PORT, TOKEN
import telebot
import redis

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT)

bot = telebot.TeleBot(TOKEN, threaded=False)