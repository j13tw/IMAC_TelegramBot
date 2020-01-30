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
group_id = config['TELEGRAM']['GROUP_ID']

# Setup Mongodb info
myMongoClient = MongoClient("mongodb://" config['MONGODB']['SERVER'] + "/")
myMongoDb = myMongoClient["smart-data-center"]
myMongoDb.authenticate(config['MONGODB']['USER'], config['MONGODB']['PASSWORD'])
dbDl303TC = myMongoDb["dl303/tc"]
dbDl303RH = myMongoDb["dl303/rh"]
dbDl303CO2 = myMongoDb["dl303/co2"]
dbDl303DP = myMongoDb["dl303/dp"]
dbEt7044 = myMongoDb["et7044"]
dbUpsA = myMongoDb["ups_a"]
dbUpsB = myMongoDb["ups_b"]
dbAirCondiction = myMongoDb["air_condiction"]
dbAirCondictionCurrent = myMongoDb["air_condiction_current"]


@app.route('/alert/<model>', methods=['POST'])
def alert(model):
    if (not (model == 'ups' or model == 'icinga' or model == 'librenms')): return {"alert": "api_model_fail"}, status.HTTP_401_UNAUTHORIZED
    if (model == 'librenms'): model = "LibreNMS"
    if (model == "icinga"): model = "IcingaWeb2"
    if (model == "ups"): model = "UPS"
    try:
        respText = "[" + model + " 監控服務異常告警]\n"
        respText += json.loads(str(request.json).replace("'", '"'))["message"]
        bot.send_message(chat_id=group_id, text=respText)
        return {"alert": "data_ok"}, status.HTTP_200_OK
    except:
        return {"alert": "data_fail"}, status.HTTP_401_UNAUTHORIZED

@app.route('/air_condiction/<module>/<sequence>', methods=['POST'])
def air_condiction_update(module, sequence):
    if request.method == 'POST':
        if (not (module == "envoriment" or module == "current")): return {"air-condiction": "api_module_fail"}, status.HTTP_401_UNAUTHORIZED 
        if (not (sequence == "a" or sequence == "b")): return {"air-condiction": "api_sequence_fail"}, status.HTTP_401_UNAUTHORIZED
        try:
            data = json.loads(str(request.json).replace("'", '"'))
            if (module == "envoriment"): 
                try:
                    data["humi"]
                    data["temp"]
                except:
                    return {"air-condiction-envoriment": "data_fail"}, status.HTTP_401_UNAUTHORIZED
            if (module == "current"):
                try:
                    data["current"]
                except:
                    return {"air-condiction-current": "data_fail"}, status.HTTP_401_UNAUTHORIZED
        except:
            return {"air-condiction": "data_fail"}, status.HTTP_401_UNAUTHORIZED
        data["sequence"] = sequence
        data["date"] = datetime.datetime.now()
        if (module == "envoriment"):
            if (dbAirCondiction.find_one({"sequence": sequence}) == None): dbAirCondiction.insert_one(data)
            else: dbAirCondiction.update_one({"sequence": sequence},{'$set':data})
            return {"ait-condiction-envoriment": "data_ok"}, status.HTTP_200_OK
        else:
            if (dbAirCondictionCurrent.find_one({"sequence": sequence}) == None): dbAirCondictionCurrent.insert_one(data)
            else: dbAirCondictionCurrent.update_one({"sequence": sequence},{'$set':data})
            return {"ait-condiction-current": "data_ok"}, status.HTTP_200_OK


@app.route('/ups/<sequence>', methods=['POST'])
def ups_update(sequence):
    if request.method == 'POST':
        if (not (sequence == "A" or sequence == "B")): return {"ups": "api_sequence_fail"}, status.HTTP_401_UNAUTHORIZED
        try:
            data = json.loads(str(request.json).replace("'", '"'))
        except:
            return {"ups": "data_fail"}, status.HTTP_401_UNAUTHORIZED
        if (sequence == "A"): dbUps = dbUpsA
        elif (sequence == "B"): dbUps = dbUpsB
        data["date"] = datetime.datetime.now()
        if (dbUps.find_one() == None): dbUps.insert_one(data)
        else: dbUps.update_one({'inputAmp': dbUps.find_one()['inputAmp']},{'$set':data})
        return {"ups": "data_ok"}, status.HTTP_200_OK

@app.route('/et7044', methods=['POST', 'GET'])
def et7044_update():
    if request.method == 'POST':
        try:
            data = json.loads(str(request.json).replace("'", '"'))
            if (not ((data['sw1'] == True or data['sw1'] == False) and (data['sw2'] == True or data['sw2'] == False) and (data['sw3'] == True or data['sw3'] == False) and (data['sw4'] == True or data['sw4'] == False) and (data['sw5'] == True or data['sw5'] == False) and (data['sw6'] == True or data['sw6'] == False) and (data['sw7'] == True or data['sw7'] == False))):
                return {"et7044": "data_info_fail"}, status.HTTP_401_UNAUTHORIZED
            data["date"] = datetime.datetime.now()
            if (dbEt7044.find_one() == None): dbEt7044.insert_one(data)
            else: dbEt7044.update_one({'sw1': dbEt7044.find_one()['sw1']}, {'$set': data})
            return {"et7044": "data_ok"}, status.HTTP_200_OK
        except:
            return {"et7044": "data_fail"}, status.HTTP_401_UNAUTHORIZED
    else:
        data = dbEt7044.find_one()
        return {"sw1": data['sw1'], "sw2": data['sw2'], "sw3": data['sw3'], "sw4": data['sw4'], "sw5": data['sw5'], "sw6": data['sw6'], "sw7": data['sw7'], "date": datetime.datetime.now()}

@app.route('/dl303/<module>', methods=['POST'])
def dl303_update(module):
    if request.method == 'POST':
        if (not (module == "tc" or module == "rh" or module == "co2" or module == "dp")): return {"dl303": "api_module_fail"}, status.HTTP_401_UNAUTHORIZED
        try: data = json.loads(str(request.json).replace("'", '"'))
        except: return {"dl303": "data_fail"}, status.HTTP_401_UNAUTHORIZED
        if (module == 'tc'):
            try:
                data['tc']
                data["date"] = datetime.datetime.now()
                if (dbDl303TC.find_one() == None): dbDl303TC.insert_one(data)
                else: dbDl303TC.update_one({'tc': dbDl303TC.find_one()['tc']}, {'$set': data})
                return {"dl303": "tc_data_ok"}, status.HTTP_200_OK
            except:
                return {"dl303": "tc_data_info_fail"}, status.HTTP_401_UNAUTHORIZED
        elif (module == 'rh'):
            try:
                data['rh']
                data["date"] = datetime.datetime.now()
                if (dbDl303RH.find_one() == None): dbDl303RH.insert_one(data)
                else: dbDl303RH.update_one({'rh': dbDl303RH.find_one()['rh']}, {'$set': data})
                return {"dl303": "rh_data_ok"}, status.HTTP_200_OK
            except:
                return {"dl303": "rh_data_info_fail"}, status.HTTP_401_UNAUTHORIZED
        elif (module == 'co2'):
            try:
                data['co2']
                data["date"] = datetime.datetime.now()
                if (dbDl303CO2.find_one() == None): dbDl303CO2.insert_one(data)
                else: dbDl303CO2.update_one({'co2': dbDl303CO2.find_one()['co2']}, {'$set': data})
                return {"dl303": "co2_data_ok"}, HTTP_200_OK
            except:
                return {"dl303": "co2_data_info_fail"}, status.HTTP_401_UNAUTHORIZED
        elif (module == 'dp'):
            try:
                data['dp']
                data["date"] = datetime.datetime.now()
                if (dbDl303DP.find_one() == None): dbDl303DP.insert_one(data)
                else: dbDl303DP.update_one({'dp': dbDl303DP.find_one()['dp']}, {'$set': data})
                return {"dl303": "dp_data_ok"}, status.HTTP_200_OK
            except:
                return {"dl303": "dp_data_info_fail"}, status.HTTP_401_UNAUTHORIZED

@app.route('/hook', methods=['POST'])
def webhook_handler():
    """Set route /hook with POST method will trigger this method."""
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        # Update dispatcher process that handler to process this message
        dispatcher.process_update(update)
    return 'ok'

def getDl303(info):
    data = "[DL303"
    dateList = []
    if (info == "all"): data += "設備狀態回報]\n"
    else: data += " 工業監測器]\n"
    if (info == "tc" or info == "all" or info == "temp/humi"):
        tc = dbDl303TC.find_one()
        dateList.append(tc['date'])
        data += "現在環境溫度: " + str(tc['tc']) + "度\n"
    if (info == "rh" or info == "all" or info == "temp/humi"):
        rh = dbDl303RH.find_one()
        dateList.append(rh['date'])
        data += "現在環境濕度: " + str(rh['rh']) + "%\n"
    if (info == "co2" or info == "all"):
        co2 = dbDl303CO2.find_one()
        dateList.append(co2['date'])
        data += "環境 CO2 濃度: " + str(co2['co2']) + "ppm\n"
    if (info == "dp" or info == "all"):
        dp = dbDl303DP.find_one()
        dateList.append(dp['date'])
        data += "環境露點溫度: " + str(dp['dp']) + "度\n"
    date = sorted(dateList)[0]
    data += "最後更新時間: \n" + str(date).split('.')[0]
    return data

def getEt7044(info):
    data = ""
    if (info == "all"): data += "[ET7044 設備狀態回報]\n"
    tmp = dbEt7044.find_one()
    if (info == "sw1" or info == "all"):
        if (tmp['sw1'] == True): sw1 = "開啟"
        else: sw1 = "關閉"
        data += "加濕器狀態: " + sw1 + "\n" 
    if (info == "sw2" or info == "all"):
        if (tmp['sw2'] == True): sw2 = "開啟"
        else: sw2 = "關閉"
        data += "進風扇狀態: " + sw2 + "\n" 
    if (info == "sw3" or info == "all"):
        if (tmp['sw3'] == True): sw3 = "開啟"
        else: sw3 = "關閉"
        data += "排風扇狀態: " + sw3 + "\n" 
    if (info == "sw4" or info == "all"):
        if (tmp['sw4'] == True): sw4 = "開啟"
        else: sw4 = "關閉"
        data += "開關 4 狀態: " + sw4 + "\n" 
    if (info == "sw5" or info == "all"):
        if (tmp['sw5'] == True): sw5 = "開啟"
        else: sw5 = "關閉"
        data += "開關 5 狀態: " + sw5 + "\n" 
    if (info == "sw6" or info == "all"):
        if (tmp['sw6'] == True): sw6 = "開啟"
        else: sw6 = "關閉"
        data += "開關 6 狀態: " + sw6 + "\n" 
    if (info == "sw7" or info == "all"):
        if (tmp['sw7'] == True): sw7 = "開啟"
        else: sw7 = "關閉"
        data += "開關 7 狀態: " + sw7 + "\n"
    data += "最後更新時間: \n" + str(tmp['date']).split('.')[0]
    return data

def getUps(device_id, info):
    if (info == "all"):
        return "ups_id = " + device_id + ", ups = all"
    elif (info == "status"):
        return "ups_id = " + device_id + ",ups = status"
    elif (info == "loading"):
        return "ups_id = " + device_id + ",ups = loading"

def getAirCondiction(device_id, info):
    data = ""
    if (info == "all"): data += "[冷氣監控狀態回報-"
    else: data += "["
    data += "冷氣" + str(device_id).upper() + "]\n"
    envoriment = dbAirCondiction.find({"sequence": device_id})[0]
    current = dbAirCondictionCurrent.find({"sequence": device_id})[0]
    if (info == "temp" or info == "all" or info == "temp/humi"):
        data += "冷氣出風口溫度: " + str(envoriment['temp']) + "度\n"
    if (info == "humi" or info == "all" or info == "temp/humi"):
        data += "冷氣出風口濕度: " + str(envoriment['humi']) + "%\n"
    if (info == "current" or info == "all"): 
        data += "冷氣功耗電流: " + str(current['current']) + " A\n"
    date = sorted([current['date'], envoriment["date"]])[0]
    data += "最後更新時間: \n" + str(date).split('.')[0]
    return data  

def reply_handler(bot, update):
    """Reply message."""
    print(dir(bot))
    print(dir(update.message))
    print(update.message.chat)
    print(update.message.chat_id)
    device_list = ['DL303', 'ET7044', 'UPS_A', 'UPS_B', '冷氣_A', '冷氣_B']
    # for s in device_list: print(s)
    text = update.message.text
    respText = ""
    if (text == '監控設備列表'): 
        text = '請選擇所需設備資訊～'
        update.message.reply_text(text, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[0:2]],
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[2:4]],
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[4:6]]
        ]))
        return
    if (text == 'DL303' or text == 'dl303'): respText = getDl303("all")
    if (text == '溫度'): respText = getDl303("tc") + "\n" + getAirCondiction("a", "temp") + "\n" + getAirCondiction("b", "temp")
    if (text == '濕度'): respText = getDl303("rh") + "\n" + getAirCondiction("a", "humi") + "\n" + getAirCondiction("b", "humi")
    if (text == '溫濕度'): respText = getDl303("temp/humi") + "\n" + getAirCondiction("a", "temp/humi") + "\n" + getAirCondiction("b", "temp/humi")
    if (text == '露點溫度'): respText = getDl303("dp")
    if (text == 'CO2'): respText = getDl303("co2")
    if (text == 'ET7044' or text == 'et7044'): respText = getEt7044("all")
    if (text == '加濕器狀態'): respText = getEt7044("sw1")
    if (text == '進風扇狀態'): respText = getEt7044("sw2")
    if (text == '排風扇狀態'): respText = getEt7044("sw3")
    if (text == '電流'): respText = getAirCondiction("a", "current") + "\n" + getAirCondiction("b", "current")
    if (text == 'UPSA狀態' or text == 'upsa狀態' or text == 'UPSA' or text == 'upsa' or text == 'UpsA' or text == 'Upsa'): respText = 'UPS_A 不斷電系統狀態\n輸入電壓:\n輸入電流:\n輸出電壓:\n輸出電流:\n輸出瓦數\n負載比例\n'
    if (text == 'UPSB狀態' or text == 'upsb狀態' or text == 'UPSB' or text == 'upsb' or text == 'UpsB' or text == 'Upsb'): respText = 'UPS_B 不斷電系統狀態\n輸入電壓:\n輸入電流:\n輸出電壓:\n輸出電流:\n輸出瓦數\n負載比例\n'
    if (text == '冷氣A狀態' or text == '冷氣a狀態' or text == '冷氣a' or text == '冷氣A'): respText = getAirCondiction("a", "all")
    if (text == '冷氣B狀態' or text == '冷氣b狀態' or text == '冷氣b' or text == '冷氣B'): respText = getAirCondiction("b", "all")
    if (text == '冷氣狀態' or text == '冷氣'): respText = getAirCondiction("a", "all") + "\n" + getAirCondiction("b", "all")

    if (respText != ""): update.message.reply_text(respText)

def device_select(bot, update):
    device = json.loads(update.callback_query.data)["device"]
    if (device == "DL303"): respText = getDl303("all")
    if (device == "ET7044"): respText = getEt7044("all")
    if (device == "UPS_A"): respText = getUps("A", "all")
    if (device == "UPS_B"): respText = getUps("B", "all")
    if (device == "冷氣_A"): respText = getAirCondiction("a", "all")
    if (device == "冷氣_B"): respText = getAirCondiction("b", "all")
    update.callback_query.message.reply_text(respText)

# New a dispatcher for bot
dispatcher = Dispatcher(bot, None)

# Add handler for handling message, there are many kinds of message. For this handler, it particular handle text
# message.

dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))
dispatcher.add_handler(CallbackQueryHandler(device_select))

if __name__ == "__main__":
    # Running server
    app.run(debug=True)
