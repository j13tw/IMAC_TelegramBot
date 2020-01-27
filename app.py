import configparser
import logging

import telegram
from flask import Flask, request
from flask_api import status
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import json
from pymongo import MongoClient
import datetime

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initial Flask app
app = Flask(__name__)

# Initial bot by Telegram access token
bot = telegram.Bot(token=(config['TELEGRAM']['ACCESS_TOKEN']))

# Setup Mongodb info
myMongoClient = MongoClient("mongodb://172.17.0.6:27017/")
myMongoDb = myMongoClient["smart-data-center"]
myMongoDb.authenticate('imac', 'imacuser')
dbDl303TC = myMongoDb["dl303/tc"]
dbDl303RH = myMongoDb["dl303/rh"]
dbDl303CO2 = myMongoDb["dl303/co2"]
dbDl303DP = myMongoDb["dl303/dp"]
dbEt7044 = myMongoDb["et7044"]
dbUpsA = myMongoDb["ups_a"]
dbUpsB = myMongoDb["ups_b"]
dbAirCondictionA = myMongoDb["air_condiction_a"]
dbAirCondictionB = myMongoDb["air_condiction_b"]


@app.route('/dl303/<module>', methods=['POST'])
def dl303_update(module):
    if request.method == 'POST':
        try:
            data = json.loads(str(request.json).replace("'", '"'))
        except:
            return {"dl303": "data_fail"}, HTTP_401_UNAUTHORIZED
        if (module == 'tc'):
            try:
                data['tc']
                data = {"tc": data['tc'], "date": datetime.datetime.now()}
                if (dbDl303TC.find_one() == None):
                    dbDl303TC.insert_one(data)
                else:
                    tmp = dbDl303TC.find_one()['tc']
                    dbDl303TC.update_one({'tc': tmp}, {'$set': data})
            except:
                return {"dl303_tc": "data_info_fail"}, HTTP_401_UNAUTHORIZED
        elif (module == 'rh'):
            try:
                data['rh']
                data = {"rh": data['rh'], "date": datetime.datetime.now()}
                if (dbDl303RH.find_one() == None):
                    dbDl303RH.insert_one(data)
                else:
                    tmp = dbDl303RH.find_one()['rh']
                    dbDl303RH.update_one({'rh': tmp}, {'$set': data})
            except:
                return {"dl303_tc": "data_info_fail"}, HTTP_401_UNAUTHORIZED
        elif (module == 'co2'):
            try:
                data['co2']
                data = {"co2": data['co2'], "date": datetime.datetime.now()}
                if (dbDl303CO2.find_one() == None):
                    dbDl303CO2.insert_one(data)
                else:
                    tmp = dbDl303CO2.find_one()['co2']
                    dbDl303CO2.update_one({'co2': tmp}, {'$set': data})`
            except:
                return {"dl303_co2": "data_info_fail"}, HTTP_401_UNAUTHORIZED
        elif (module == 'dp'):
            try:
                data['dp']
                data = {"dp": data['dp'], "date": datetime.datetime.now()}
                if (dbDl303DP.find_one() == None):
                    dbDl303DP.insert_one(data)
                else:
                    tmp = dbDl303DP.find_one()['dp']
                    dbDl303DP.update_one({'dp': tmp}, {'$set': data})
            except:
                return {"dl303_dp": "data_info_fail"}, HTTP_401_UNAUTHORIZED

@app.route('/hook', methods=['POST'])
def webhook_handler():
    """Set route /hook with POST method will trigger this method."""
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        # Update dispatcher process that handler to process this message
        dispatcher.process_update(update)
    return 'ok'

def getDl303(info):
    data = ""
    if (info == "all"): data += "DL303 設備狀態回報:\n"
    if (info == "tc" or info == "all"):
        tc = dbDl303TC.find_one()
        data += "現在溫度: " + str(tc['tc']) + "度\n最後更新時間: " + str(tc['date']).split('.')[0] + "\n"
    if (info == "rh" or info == "all"):
        rh = dbDl303RH.find_one()
        data += "現在濕度: " + str(rh['rh']) + "%\n最後更新時間: " + str(rh['date']).split('.')[0] + "\n"
    if (info == "co2" or info == "all"):
        co2 = dbDl303CO2.find_one()
        data += "CO2 濃度: " + str(co2['co2']) + "ppm\n最後更新時間: " + str(co2['date']).split('.')[0] + "\n"
    if (info == "dp" or info == "all"):
        dp = dbDl303DP.find_one()
        data += "露點溫度: " + str(dp['dp']) + "度\n最後更新時間: " + str(dp['date']).split('.')[0] + "\n"
    return data

def getEt7044(info):
    if (info == "all"):
        return "et7044 = get_all"
    elif (info == "sw1"):
        return "et7044 = get_sw1"
    elif (info == "sw2"):
        return "et7044 = get_sw2"
    elif (info == "sw3"):
        return "et7044 = get_sw3"
    elif (info == "sw4"):
        return "et7044 = get_sw4"
    elif (info == "sw5"):
        return "et7044 = get_sw5"
    elif (info == "sw6"):
        return "et7044 = get_sw6"
    elif (info == "sw7"):
        return "et7044 = get_sw7"
    else:
        return "et7044 = fail" 

def getUps(device_id, info):
    if (info == "all"):
        return "ups_id = " + device_id + ", ups = all"
    elif (info == "status"):
        return "ups_id = " + device_id + ",ups = status"
    elif (info == "loading"):
        return "ups_id = " + device_id + ",ups = loading"

def getAitCondiction(device_id, info):
    if (info == "all"):
        return "air_condiction_id = " + device_id +",air_condiction = all"
    elif (info == "temp"):
        return "air_condiction_id = " + device_id +",air_condiction = temp"
    elif (info == "humi"):
        return "air_condiction_id = " + device_id +",air_condiction = humi"
    elif (info == "current"):
        return "air_condiction_id = " + device_id +",air_condiction = current"


def reply_handler(bot, update):
    """Reply message."""
    print(dir(update.message))
    device_list = ['DL303', 'ET7044', 'UPS_A', 'UPS_B', '冷氣_A', '冷氣_B']
    # for s in device_list: print(s)
    text = update.message.text
    if (text == '監控設備列表'): 
        text = '請選擇所需設備資訊～'
        update.message.reply_text(text, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[0:2]],
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[2:4]],
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[4:6]]
        ]))
        return
    if (text == 'DL303'): text = getDl303("all")
    if (text == '溫度'): text = getDl303("tc")
    if (text == '濕度'): text = getDl303("rh")
    if (text == '露點溫度'): text = getDl303("dp")
    if (text == 'CO2'): text = getDl303("co2")
    if (text == '電流'): text = '現在電流狀態:\n冷氣_A: 15 A\n 冷氣_B: 0A\nUPS_A(牆壁): 10.5 A\nUPS_B(窗戶): 12.5A'
    if (text == 'UPS_A 狀態'): text = 'UPS_A 不斷電系統狀態\n輸入電壓:\n輸入電流:\n輸出電壓:\n輸出電流:\n輸出瓦數\n負載比例\n'
    if (text == 'UPS_B 狀態'): text = 'UPS_B 不斷電系統狀態\n輸入電壓:\n輸入電流:\n輸出電壓:\n輸出電流:\n輸出瓦數\n負載比例\n'
    if (text == '冷氣_A 狀態'): text = '冷氣_A 空調狀態\n出風口溫度: 10度\n功耗電流: 20 A'
    if (text == '冷氣_B 狀態'): text = '冷氣_B 空調狀態\n出風口溫度: 10度\n功耗電流: 20 A'
    update.message.reply_text(text)

def device_select(bot, update):
    device = json.loads(update.callback_query.data)["device"]
    print(device)
    if (device == "DL303"): text = getDl303("all")
    if (device == "ET7044"): text = getEt7044("all")
    if (device == "UPS_A"): text = getUps("A", "all")
    if (device == "UPS_B"): text = getUps("B", "all")
    if (device == "冷氣_A"): text = getAitCondiction("A", "all")
    if (device == "冷氣_B"): text = getAitCondiction("B", "all")
    print(device ,text)
    update.callback_query.edit_message_text(text)

# New a dispatcher for bot
dispatcher = Dispatcher(bot, None)

# Add handler for handling message, there are many kinds of message. For this handler, it particular handle text
# message.

dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))
dispatcher.add_handler(CallbackQueryHandler(device_select))

if __name__ == "__main__":
    # Running server
    app.run(debug=True)
