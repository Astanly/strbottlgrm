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

import json
import time
import requests
import urllib

from flask import Flask, request, redirect, session, url_for

from flask_sqlalchemy import SQLAlchemy
from requests_oauthlib import OAuth2Session
from telebot import types
from datetime import datetime
import config
import urllib.request
import urllib.parse
from sqlalchemy import exc
from telegraph import Telegraph
from jinja2 import Environment, PackageLoader, select_autoescape
#### начало проррамы 143 линия

#убрать в отдельный файл
TOKEN=config.TOKEN
bot = telebot.TeleBot(config.TOKEN, threaded=False)
client_id = config.client_id
client_secret = config.client_secret
scope =  'activity:read_all,activity:write,profile:read_all,profile:write'
authorization_base_url = 'https://www.strava.com/oauth/authorize'
token_url = 'https://www.strava.com/oauth/token'
refresh_url = 'https://www.strava.com/oauth/token'
response_typ = 'code'
redirect_uri = config.redirect_uri# Should match Site URL
start_uri = config.start_uri
webhook_uri=config.webhook_uri
tranings_list= ["AlpineSki", "BackcountrySki", "Canoeing", "Crossfit", "EBikeRide", "Elliptical", "Golf",
               "Handcycle", "Hike", "IceSkate", "InlineSkate", "Kayaking", "Kitesurf", "NordicSki",
               "Ride", "RockClimbing", "RollerSki", "Rowing, Run", "Sail, Skateboard", "Snowboard",
               "Snowshoe", "Soccer", "StairStepper", "StandUpPaddling", "Surfing", "Swim", "Velomobile",
               "VirtualRide", "VirtualRun", "Walk", "WeightTraining", "Wheelchair", "Windsurf", "Workout", "Yoga"]
Options_list= ["Display_last_10_trainigs","Display last 10 trainigs by activity type"," My year stat","my all time stat"]
keys_list_ride=['type','name','average_heartrate', 'average_speed',"average_watts", "max_heartrate", " max_watts", "id" ]

env = Environment( loader=PackageLoader('mysite', 'Template'), autoescape=select_autoescape(['html', 'xml']))

template = env.get_template('1.html')
###
app = Flask(__name__)
app.secret_key = config.key
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 200
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
temp_data_dict={}
bot.enable_save_next_step_handlers(delay=2)

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

@app.route('/data/<int:v_int>')
def data(v_int):
   f=request.args.get("s_data")
   f.encode("utf-8")
   v=json.loads(f)
   g=template.render(data=v)
   return (g)

#### работа с сайтом
@app.route("/")
def bu():
     return("<h1> Privet <h1>")

@app.route("/login", methods=["GET","POST"])
def login1():
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
    stravalogin = OAuth2Session(client_id)
    token = stravalogin.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)
    print(session)
    from jinja92 import Template
    print(session)
    session['oauth_token'] = token
    acces_test = User_filter_by_chat_id(message_chat_id, token["athlete"].get("firstname", "Кто-то без имени"), token['access_token'], token['refresh_token'])
    t= Template("Hello {{ name }}!")
    time.sleep(20)
    if acces_test.Is_Exsist() == False:
      if acces_test.acces_test():
         acces_test.new_profile()
      else:
         bot.send_message(message_chat_id, "Why you see this mmesse???? WHY????????  pls Open activity read all ")
         acces_test.login()
    else: pass

    return  (t.render(name= session['oauth_token']["athlete"].get("firstname", "мы еще не знакомы")))

# @app.route("/refresh_token", methods=["GET","POST"])
# def refresh_token():
#     messagechatid=request.args.get('message.chat.id', None)

@app.route("/webhook" + TOKEN, methods=['POST'])
def getMessage():
    #обраотчик веб хука

    if request.headers.get('content-type') == 'application/json':
      json_string = request.get_data().decode('utf-8')
      update = telebot.types.Update.de_json(json_string)

      time.sleep(2)
      bot.process_new_updates([update])
      return 'bubju'

@app.route("/webhook", methods=["GET","POST"])
def webhook():
###тавим веб хук для бота надо вызывать это сайт из браузера
    bot.remove_webhook()
    bot.set_webhook(url=webhook_uri + TOKEN)
    return ("!", 200)

def trainigslist_get():
    keyboard1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
#    to_sent1 = f"lasttrainigN:Ride:{token}"
#    to_sent2 = f"lasttrainigN:Run:{token}"
#    to_sent3 = f"lasttrainigN:Swim:{token}"
#    to_sent4 = f"lasttrainigN:VirtualRide:{token}"
    button1 = types.InlineKeyboardButton(text= "Bike", callback_data=to_sent )
    button2 = types.InlineKeyboardButton(text= "Run", callback_data=to_sent1 )
    button3 = types.InlineKeyboardButton(text= "Swim", callback_data=to_sent2 )
    button4 = types.InlineKeyboardButton(text= "VirtualRide", callback_data=to_sent3 )

    keyboard1.add(button1, button2 , button3,button4)
    bot.send_message(session["message.chat.id"], "chouse to see last trainigs", reply_markup=keyboard1)


  #  return (t.render(something= r["firstname"]))

def sent_filtered_data(num, chat_id, query_string=1):

                sent= "Название тренировки {} \n тип тренироки {} \n максимальный пульс {} \n средняя мощность {}".format(num["name"],
                                                                                                                          num["type"],
                                                                                                                          num.get("max_heartrate", "нэт его") ,
                                                                                                                          num.get("average_watts", "в нет"))
                bot.send_message(chat_id, sent)



class User_filter_by_chat_id():
    def __init__(self, chat_id, name= None, token = None, refresh_token = None):
         self.chat_id=chat_id
         if token and refresh_token and name:
            self.token = token
            self.refresh_token=refresh_token
            self.name=name
            self.user_to_find = StravaUser.query.filter_by(telegram_chat_id=self.chat_id).first()
         else:
            try:
                   self.user_to_find = StravaUser.query.filter_by(telegram_chat_id=self.chat_id).first()
                   if self.user_to_find :
                      self.token = self.user_to_find.token
                      self.refresh_token=self.user_to_find.refresh_token
                      self.name = self.user_to_find.username
                   else:
                       pass
            except exc.SQLAlchemyError as e:
                 bot.send_message(self.chat_id, "SQL data base failed FML")

    def Is_Exsist(self):
         if self.user_to_find:
             return True
         else:
             return False
    def username(self):
        return self.user_to_find.username
    def last_seen(self):
        return self.user_to_find.last_seen
    def refresh_data(self):
        print('refreshing db')
        self.user_to_find.token= self.token
        self.user_to_find.refresh_token=self.refresh_token
        self.user_to_find.last_seen= datetime.utcnow
        db.session.commit()
    def del_user(self):
        db.session.delete(self.user_to_find)
        db.session.commit()

    def manual_refresh(self):
        extra = {
        'client_id': client_id,
        'client_secret': client_secret,
                 }
        strava = OAuth2Session (client_id, )
        v = strava.refresh_token(refresh_url, refresh_token=self.user_to_find.refresh_token, **extra)
        db.session.merge(self.user_to_find)
        self.user_to_find.token= v.get("access_token", "no_data")
        self.user_to_find.refresh_token=v["refresh_token"]
        db.session.commit()
        print(self.refresh_token)

    def acces_test(self, page=1 ,per_page=1):
      try:
        url="https://www.strava.com/api/v3/athlete/activities"
        param={"per_page":f"{per_page}","page":f"{page}"}
        headers = {'Authorization': "Bearer "+self.token}
        initial_response=requests.get(url, params=param, headers = headers, allow_redirects=False)
        data2=initial_response.json()
        print("geting acces")
        if initial_response.status_code == requests.codes.ok:
                 print(data2)
                 return(True)
        if initial_response.headers.get("status") ==  "401 Unauthorized":
                 return (None)
      except requests.exceptions.ConnectionError as e:
             print( "Error: on url {}".format(e))

    def login(self):
         keyboard = types.InlineKeyboardMarkup()
         params = urllib.parse.urlencode({'message.chat.id': self.chat_id})
         uri = start_uri+params
         url_button = types.InlineKeyboardButton(text="залогиниться в стравe", url=uri)
         keyboard.add(url_button)
         bot.send_message(self.chat_id, "Привет! Нажми на кнопку и перейди в eбучую страву.", reply_markup=keyboard)
         return (True)
    def new_profile(self):
         new_user=StravaUser(self.name, self.chat_id, self.token, self.refresh_token)
         db.session.add(new_user)
         try:
            db.session.commit()
         except exc.SQLAlchemyError:
            bot.send_message(self.chat_id, "SQL data base failed FML")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Hello,this is strava bot one day your could analize strava in telegram. now days run in test mode ')
    ######### Вот и начинается ебалала блять как передать mesage chat id в @app.route("/login")
    user=User_filter_by_chat_id(message.chat.id)
    if user.Is_Exsist():
       bot.send_message(message.chat.id, 'Hello old friend {}'.format(user.username()), reply_markup=types.ReplyKeyboardRemove())
       firstlist(message.chat.id)
    else:
       user.login()

@bot.message_handler(commands=['stop'])
def del_use(message):
     user_del=User_filter_by_chat_id(message.chat.id)
     if user_del.Is_Exsist():
       bot.send_message(message.chat.id, 'By old friend {} '.format(user_del.username()), reply_markup=types.ReplyKeyboardRemove())
       user_del.del_user()
     else:
       bot.send_message(message.chat.id, "If dog doen't sheet it will exsplloed\n Create new account first",reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['revoke_token'])
def revoke_token(message):
    bot.send_message(message.chat.id, 'problems? ')
    ######### Вот и начинается ебалала блять как передать mesage chat id в @app.route("/login")
    user=User_filter_by_chat_id(message.chat.id)
    print(user)
    if user.Is_Exsist():
       bot.send_message(message.chat.id, 'Hello old friend {} revoking your token'.format(user.username()), reply_markup=types.ReplyKeyboardRemove())
       user.manual_refresh()
    else:
       user.login()


### тут уже обработчик  стравы api тож  в отдельный класс
def getlasttrainigs(chat_id, page=1 ,days_to_search=10, activity=True, efforts=True):
    try:
        print("gettonglast_traings")
        new_user=User_filter_by_chat_id(chat_id)
        token= new_user.token
        print(token)
        url="https://www.strava.com/api/v3/athlete/activities"
        param={"per_page":"200","page":f"{page}"}
        headers = {'Authorization': "Bearer "+token}
        initial_response=requests.get(url, params=param, headers = headers, allow_redirects=False)
        data2=initial_response.json()
        bot.send_chat_action(chat_id, 'typing')  # show the bot "typing" (max. 5 secs)
        if initial_response.status_code == requests.codes.ok:
            ##print(data2)

            return (data2)
        else:
           try:
               new_user.manual_refresh()
               bot.send_message(chat_id, "updating token")
               token1 = new_user.token
               headers1 = {'Authorization': "Bearer "+token1}
               print(token)
               initial_response=requests.get(url, params=param, headers = headers1, allow_redirects=False)
               data2=initial_response.json()
               bot.send_chat_action(chat_id, 'typing')  # show the bot "typing" (max. 5 secs)
               return(data2)
           except requests.exceptions.ConnectionError as e:
                  bot.send_message(chat_id, "OOOOPPPS some errors with token pls log_out and login, {}".format(e))
                  return (None)

    except requests.exceptions.ConnectionError as e:
          #print(r.url)
        bot.send_message(chat_id, "OOOOPPPS some errors with token pls log_out and login, {}".format(e))



def sent_last_trainigs(message,step=0 ,activiteis=50 ):
    # отправляем тока RIde i vyvodim puls i power
         chat_id=message.chat.id
         activiteis=activiteis
         print(message.text)
         if message.text in tranings_list:
            tupe = message.text
         if message.text == "back":
            firstlist(chat_id)
         if message.text == "/Start":
            firstlist(chat_id)
         bot.send_chat_action(chat_id, 'typing')  # show the bot "typing" (max. 5 secs)
         print("tupe fromsecon click{}".format(tupe))
         listdata, step =list_get(chat_id, step,activiteis=activiteis, filtrer_act = tupe, filter_off= False)
         list_to_sent=sent_url_post(preSort(listdata))
         print(list_to_sent)
         bot.send_message(message.chat.id, "{}".format(list_to_sent))
         #dict_new= json.dumps(preSort(listdata))
         #sent_url=url_for('data',v_int =1213214,s_data = dict_new)
         #bot.send_message(message.chat.id, "http://astanly.pythonanywhere.com{}".format(sent_url))
         keyboard1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
         [keyboard1.add(i) for i in ["back", f"{message.text}"]]
         msg=bot.send_message(message.chat.id, "What shoud i do next?\n To see more data press {}{}".format(message.text, step), reply_markup=keyboard1)
         if step >= 0:
            step+=1
         bot.register_next_step_handler(msg, sent_last_trainigs, step=step,activiteis=activiteis  )

def list_get(chat_id,step,filtrer_act,filter_off, activiteis=50):
    # отправляем тока RIde i vyvodim puls i power
     chat_id=chat_id
     page=0
     v=[]

     if all([chat_id in temp_data_dict, step>0]):
        train_list=temp_data_dict[chat_id]
        print(train_list)
        page=train_list[step-1]["step"]["page"]
        v=train_list[step-1]["step"]["data"]
     if step ==0:
        d=[]
        temp_data_dict[chat_id]=d
     bot.send_message(chat_id, "filtering activities")
     while len(v)<(activiteis+activiteis*step):
       page+=1
       if page < (20+20*step):
         listdata=getlasttrainigs(chat_id,page)
         bot.send_chat_action(chat_id, 'typing')  # show the bot "typing" (max. 5 secs)
         i= [num for num in listdata if  any([num["type"]== filtrer_act, filter_off==True])]
         v.extend(i)
       else:
         bot.send_message(chat_id, "In your 400 activivteies \n only {} found ".format(len(v)))
         step=-1
         break
     if len(v)>0:
        temp_dict={"step":{"data":v, "length":len(v), "page":page}}
        temp_list=temp_data_dict[chat_id]
        temp_list.append(temp_dict)
        temp_data_dict[chat_id]=temp_list
     if step == 0:
       print( "step{}".format(step))
       try:
          del v[activiteis:len(v)]
       except:
          pass
     if step == -2:
         bot.send_message(chat_id, "we are going to reach singularity!??")
     if step > 0:
        try:
          del v[(activiteis*step+activiteis):len(v)]
          del v[0:activiteis*step]
          if len(v)<activiteis:
             step=-1

        except:
          pass

     return (v,step)




def preSort(m):

    list_new=[]
    for i in m:
        dict_new={key: val for  key, val  in i.items() if key in keys_list_ride}
        print(dict_new)
        list_new.append(dict_new)
    print(list_new)
    return(list_new)

def sent_url_post(data_to_sent):
    m=template.render(data=data_to_sent)
    print (m)
    telegraph = Telegraph()
    telegraph.create_account(short_name="starava_bot")
    response = telegraph.create_page('ioiioio data',html_content=m)
    print(response)
    return('https://telegra.ph/{}'.format(response['path']))

def trainigslist(message):
    if message.text == "Display last 10 trainigs by activity type":
      keyboard1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
      for i in tranings_list:
        keyboard1.add(i)
      msg1=bot.send_message(message.chat.id, "choose activite to getlist to see last trainigs", reply_markup=keyboard1)
      bot.register_next_step_handler(msg1, sent_last_trainigs,step=0)
    if message.text == "Display_last_10_trainigs":
       listdata=list_get(message.chat.id, activiteis=10,filter_act="blabla", filter_off= True )
         #list_to_sent=sent_url_post(preSort(listdata))
         #bot.send_message(message.chat.id, "{}".format(list_to_sent))
       dict_new= json.dumps(preSort(listdata))
       sent_url=url_for('data',v_int =1213214,s_data = dict_new)
       bot.send_message(message.chat.id, "http://astanly.pythonanywhere.com{}".format(sent_url))
       firstlist(message.chat.id, msg_1 ="what_next")
    if message.text == "back":
       firstlist(message.chat.id, msg_1 ="what_next")

def firstlist(chat_id, msg_1="chouse to see last trainigs"):
    keyboard1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for i in Options_list:
       keyboard1.add(i)
    keyboard1.add("back")
    msg=bot.send_message(chat_id, msg_1, reply_markup=keyboard1)
    bot.register_next_step_handler(msg, trainigslist)


if __name__ == '__main__':
     app.run(threaded=False)

