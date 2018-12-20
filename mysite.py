#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      andr.stankevich
#
# Created:     28.11.2018
# Copyright:   (c) andr.stankevich 2018
# Licence:     <your licence>
#------------------------------------------------------------------------
import telebot
import httplib2
import json
import sys
import time
import requests
import urllib
import os
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from requests_oauthlib import OAuth2Session
from telebot import types
#from datetime import datetime, timedelta
import config
import urllib.request
import urllib.parse
#### начало проррамы 143 линия

#убрать нахуй в отдельный файл
TOKEN=config.TOKEN
bot = telebot.TeleBot(config.TOKEN, threaded=False)
client_id = config.client_id
client_secret = config.client_secret
scope =  'activity:read_all,activity:write,profile:read_all,profile:write'
authorization_base_url = 'https://www.strava.com/oauth/authorize'
token_url = 'https://www.strava.com/oauth/token'
response_typ = 'code'
redirect_uri = config.redirect_uri# Should match Site URL
start_uri = config.start_uri
webhook_uri=config.webhook_uri
###






app = Flask(__name__)
app.secret_key = config.key



#### работа с сайтом
@app.route("/")
def bu():
     return("<h1> Privet <h1>")

@app.route("/login", methods=["GET","POST"])
def login():

     messagechatid=request.args.get('message.chat.id', None)
     print(messagechatid)
     # """Step 1: User Authorization. Redirect the user/resource owner to the OAuth provider (i.e. Strava) using an URL with a few key OAuth parameters."""
     strava = OAuth2Session(client_id,scope=scope,redirect_uri=redirect_uri)

     authorization_url, state =strava.authorization_url(authorization_base_url)
     #authorization_url =strava.authorization_url(authorization_base_url)
     print(authorization_url)
     session['message.chat.id']=messagechatid
     session['oauth_state'] = state
     return redirect(authorization_url)

@app.route("/callback", methods=["GET","POST"])
def callback():

    try:
        stravalogin = OAuth2Session(client_id)
        token = stravalogin.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

        # bot.send_message(session["message.chat.id"], "Нigh from callback")
        print (f"token from callback is {token}")
    except requests.RequestException as e:
        print("eroor")
    from jinja2 import Template
    session['oauth_token'] = token
    print (token)
    t= Template("Hello {{ something }}!")
    time.sleep(20)
    profile()
    return  (t.render(something= session.get("firstname", "мы еще не знакомы")))

@app.route("/webhook" + TOKEN, methods=['POST'])
def getMessage():
    #обраотчик веб хука
    if request.headers.get('content-type') == 'application/json':
    #print(request.headers.get)
      json_string = request.get_data().decode('utf-8')
    #print(json_string)
      update = telebot.types.Update.de_json(json_string)
      bot.process_new_updates([update])
      return ''



@app.route("/webhook", methods=["GET","POST"])
def webhook():
###тавим веб хук для бота надо вызывать это сайт из браузера
    bot.remove_webhook()
    bot.set_webhook(url=webhook_uri + TOKEN)
    return ("!", 200)

#@app.route("/profile", methods=["GET"])
def profile():

### подключаемся к страве и тяним имя и токен хуеукен
    strava = OAuth2Session( token=session['oauth_token'])
    r=strava.get('https://www.strava.com/api/v3/athlete').json()
    from jinja2 import Template
    print(session['oauth_token'])
    token = session['oauth_token']['access_token']
    print (token)
    t= Template("Hello {{ something }}!")
     #UserName = "{} {}".format(r["firstname"],r["lastname"])
    keyboard1 = types.InlineKeyboardMarkup()
    to_sent = f"lasttrainigN:Ride:{token}"
    to_sent1 = f"lasttrainigN:Run:{token}"
    to_sent2 = f"lasttrainigN:Swim:{token}"
    button1 = types.InlineKeyboardButton(text= "Bike", callback_data=to_sent )
    button2 = types.InlineKeyboardButton(text= "Run", callback_data=to_sent1 )
    button3 = types.InlineKeyboardButton(text= "Swim", callback_data=to_sent2 )

    keyboard1.add(button1, button2 , button3)
    bot.send_message(session["message.chat.id"], "chouse to see last trainigs", reply_markup=keyboard1)


  #  return (t.render(something= r["firstname"]))



@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Hello,this is strava bot one day your could analize strava in telegram. now days run in test mode ')
    ######### Вот и начинается ебалала блять как передать mesage chat id в @app.route("/login")
    login_1(message.chat.id)





@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # отправляем тока RIde i vyvodim puls i power
      if  'lasttrainigN' in call.data:
         chat_id=call.message.chat.id
         print(call.data)
         title, tupe ,token = call.data.split(':')
         data2=getlasttrainigs(token,chat_id)
         for num, key in enumerate(data2) :
            data1=data2[num]
            if  data1.get("type", "нихуянет") == tupe:

                ##if {'max_heartrate','average_watts'} <=data1.keys() :
                sent= "Название тренировки {} \n тип тренироки {} \n максимальный пульс {} \n средняя мощность {}".format(data1["name"],
                                                                                                                  data1["type"],
                                                                                                                  data1.get("max_heartrate", "нэт его") ,
                                                                                                                  data1.get("average_watts", "в проебе"))
                bot.send_message(chat_id, sent)

            else: num
### тут уже обработчик  стравы api тож нахуй в отдельный класс
def getlasttrainigs(token, chat_id, page=1 ,days_to_search=10, activity="ride", efforts="true"):
    try:
     #   timestop =round((datetime.now()-timedelta(days=days_to_search)).timestamp())
      #  timestart=round(datetime.now().timestamp())
        url="https://www.strava.com/api/v3/athlete/activities"
        param={"per_page":"20","page":f"{page}"}
        headers = {'Authorization': "Bearer "+token}
        initial_response=requests.get(url, params=param, headers = headers, allow_redirects=False)
        data2=initial_response.json()
        if initial_response.headers.get("status") ==  "401 Unauthorized":
                 bot.send_message(chat_id, "блять ты заебал что можно увидеть если не открыть трени!!! не перегружай сервак или пиши свой код")
                 return (False)

        if initial_response.status_code == requests.codes.ok:
                 return (data2)
        else:    return (False)
    except requests.exceptions.ConnectionError as e:
          #print(r.url)
        print( "Error: on url {}".format(e))

def login_1(chat_id):
    keyboard = types.InlineKeyboardMarkup()

    params = urllib.parse.urlencode({'message.chat.id': chat_id})
    print(params)
    uri = start_uri+params
    url_button = types.InlineKeyboardButton(text="залогиниться в стравe", url=uri)
    keyboard.add(url_button)
    bot.send_message(chat_id, "Привет! Нажми на кнопку и перейди в eбучую страву.", reply_markup=keyboard)
    return (True)







if __name__ == '__main__':

     app.run(threaded=True)


