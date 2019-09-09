# How to start badcamp for local development
## Requirements
You need ngrok and docker installed on your system and telegram bot for testing:
* ngrok: https://ngrok.com/download
* docker: https://docs.docker.com/install/linux/docker-ce/ubuntu
* telegram: https://core.telegram.org/bots#6-botfather

## Badcamp local installation
* start ngrok on port 5000
```
ngrok http 5000
```
* create file localsettings.py
```
REDIS_HOST = 'redis'
REDIS_PORT = 6379
RABBIT = {'AMQP_URI': "amqp://guest:guest@rabbit"}
UPLOAD_DIR = '/tmp'
TOKEN = '****' #bot token
WEBHOOK_URL = 'https://214619b8.ngrok.io' #change it to your ngrok tunnel host
```

* Build docker containers
```
docker-compose build
```
* Start docker containers
```
docker-compose up
```
* Start nameko service 
```
sudo docker exec -it badcamp_app_1 nameko run service --broker amqp://guest:guest@rabbit &
```
* Set telegram api webhook
```
https://api.telegram.org/bot{TOKEN}/setWebhook?url={NGROK URL}
```

you are good to go now 
