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
from flask_sqlalchemy import SQLAlchemy
from requests_oauthlib import OAuth2Session
from telebot import types
from datetime import datetime, timedelta
import config
import urllib.request
import urllib.parse
from sqlalchemy import exc
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
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 200
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class StravaUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    telegram_chat_id = db.Column(db.String(120), unique=True)
    token = db.Column(db.String(120), unique=True)
    refresh_token= db.Column(db.String(120), unique=True)
    last_seen= db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __init__(self, username, telegram_chat_id, token, refresh_token):
        self.username = username
        self.telegram_chat_id =telegram_chat_id
        self.token=token
        self.refresh_token=refresh_token

    def __repr__(self):
        return '<User %r>' % self.username


#### работа с сайтом
@app.route("/")
def bu():
     return("<h1> Privet <h1>")

@app.route("/login", methods=["GET","POST"])
def login():
     messagechatid=request.args.get('message.chat.id', None)
     # """Step 1: User Authorization. Redirect the user/resource owner to the OAuth provider (i.e. Strava) using an URL with a few key OAuth parameters."""
     strava = OAuth2Session(client_id,scope=scope,redirect_uri=redirect_uri)
     authorization_url, state =strava.authorization_url(authorization_base_url)
     session['message.chat.id']=messagechatid
     session['oauth_state'] = state
     return redirect(authorization_url)
@app.route("/callback", methods=["GET","POST"])
def callback():
    #print (request.args())
    print(session)
    message_chat_id=session["message.chat.id"]
    try:
        stravalogin = OAuth2Session(client_id)
        token = stravalogin.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

        print(session)


    except requests.RequestException as e:
        print("eroor")
    from jinja2 import Template
    print(session)
    session['oauth_token'] = token
    acces_test = StravaRequestUser(message_chat_id, session['oauth_token']['access_token'], session['oauth_token']['refresh_token'])
    t= Template("Hello {{ name }}!")
    time.sleep(20)
    if acces_test.acces_test():
       new_profile()
    else:
       login_1(message_chat_id)
    return  (t.render(name= session['oauth_token']["athlete"].get("firstname", "мы еще не знакомы")))

@app.route("/webhook" + TOKEN, methods=['POST'])
def getMessage():
    #обраотчик веб хука
    if request.headers.get('content-type') == 'application/json':
    #print(request.headers.get)
      json_string = request.get_data().decode('utf-8')
    #print(json_string)
      update = telebot.types.Update.de_json(json_string)
      bot.process_new_updates([update])
      return 'bubju'



@app.route("/webhook", methods=["GET","POST"])
def webhook():
###тавим веб хук для бота надо вызывать это сайт из браузера
    bot.remove_webhook()
    bot.set_webhook(url=webhook_uri + TOKEN)
    return ("!", 200)


def new_profile():
    #strava = OAuth2Session(token=session['oauth_token'])
    # print(session)
    print(session)
    token = session['oauth_token']['access_token']
    refresh_token= session['oauth_token']['refresh_token']
    telegram_chat_id=session["message.chat.id"]
    Name = session['oauth_token']['athlete']['username']

    new_user=StravaUser( Name, telegram_chat_id,token, refresh_token)
    db.session.add(new_user)
    try:

        db.session.commit()
    except exc.SQLAlchemyError:
        bot.send_message(telegram_chat_id, "SQL data base failed FML")

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
    user=User_filter_by_chat_id(message.chat.id)
    print(user)
    if user.Is_Exsist():
       bot.send_message(message.chat.id, 'Hello old friend {}'.format(user.username()))
    else:
       login_1(message.chat.id)
@bot.message_handler(commands=['stop'])
def del_use(message):
     user_del=User_filter_by_chat_id(message.chat.id)
     if user_del.Is_Exsist():
       bot.send_message(message.chat.id, 'By old friend {} '.format(user_del.username()))
       user_del.del_user()
     else:
       bot.send_message(message.chat.id, "If dog doen't sheet it will exsplloed\n Create new account first")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # отправляем тока RIde i vyvodim puls i power
      if  'lasttrainigN' in call.data:
         chat_id=call.message.chat.id
         print(call.data)
         title, tupe ,token = call.data.split(':')
         data2=getlasttrainigs(token,chat_id)
         if data2:
            print (data2)
            [sent_filtered_data(num,chat_id)  for  num in data2 if num["type"]== tupe]

def sent_filtered_data(num, chat_id, query_string=1):

                sent= "Название тренировки {} \n тип тренироки {} \n максимальный пульс {} \n средняя мощность {}".format(num["name"],
                                                                                                                          num["type"],
                                                                                                                          num.get("max_heartrate", "нэт его") ,
                                                                                                                          num.get("average_watts", "в проебе"))
                bot.send_message(chat_id, sent)

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
        if initial_response.status_code == requests.codes.ok:
                 print(data2)
                 return (data2)
        if initial_response.headers.get("status") ==  "401 Unauthorized":
                 bot.send_message(chat_id, "блять? что можно увидеть если не открыть трени!!! н")
                 login_1(chat_id)
                 return (None)

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

class User_filter_by_chat_id():
    def __init__(self, chat_id):
         self.chat_id=chat_id
         try:
              self.user_to_find = StravaUser.query.filter_by(telegram_chat_id=self.chat_id).first()
         except exc.SQLAlchemyError:
              bot.send_message(self.chat_id, "SQL data base failed FML")
    def Is_Exsist(self):
         if self.user_to_find == None:
             return False
         else:
             return True
    def token(self):
        return self.user_to_find.token
    def refresh_token(self):
        return self.user_to_find.refresh_token
    def username(self):
        return self.user_to_find.username
    def last_seen(self):
        return self.user_to_find.last_seen
    def refresh_data(self, token, refresh_token):
        self.user_to_find.token= token
        self.user_to_find.refresh_token=refresh_token
        self.user_to_find.last_seen= datetime.utcnow
        db.session.commit()
    def del_user(self):
        db.session.delete(self.user_to_find)
        db.session.commit()

class StravaRequestUser():
    def __init__(self, chat_id, token, refresh_token):
        self.chat_id=chat_id
        self.token = token
        self.refresh_token=refresh_token
    def acces_test(self, page=1 ,per_page=1):
      try:
        url="https://www.strava.com/api/v3/athlete/activities"
        param={"per_page":f"{per_page}","page":f"{page}"}
        headers = {'Authorization': "Bearer "+self.token}
        initial_response=requests.get(url, params=param, headers = headers, allow_redirects=False)
        data2=initial_response.json()
        if initial_response.status_code == requests.codes.ok:
                 print(data2)
                 return(data2)
        if initial_response.headers.get("status") ==  "401 Unauthorized":
                 return (None)
      except requests.exceptions.ConnectionError as e:
          #print(r.url)
        print( "Error: on url {}".format(e))
   def refresh_token





if __name__ == '__main__':

     app.run(threaded=True)


