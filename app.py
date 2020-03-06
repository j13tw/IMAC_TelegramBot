import configparser
import logging

import telegram
from flask import Flask, request
from flask_api import status
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import json
from pymongo import MongoClient
import datetime
import time

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

# Setup user & group id for reply specify message
group_id = int(config['TELEGRAM']['GROUP_ID'])
devUser_id = int(config['TELEGRAM']['DEV_USER_ID'])

dl303_owner = int(config['DEVICE']['DL303_OWNER'])
et7044_owner = int(config['DEVICE']['ET7044_OWNER'])
ups_owner = int(config['DEVICE']['UPS_OWNER'])
air_condiction_owner = int(config['DEVICE']['AIR_CONDICTION_OWNER'])

# Setup Mongodb info
myMongoClient = MongoClient(config['MONGODB']['SERVER_PROTOCOL'] + "://" + config['MONGODB']['USER'] + ":" + config['MONGODB']['PASSWORD'] + "@" + config['MONGODB']['SERVER'])
myMongoDb = myMongoClient["smart-data-center"]
# myMongoDb.authenticate(config['MONGODB']['USER'], config['MONGODB']['PASSWORD'])
dbDl303TC = myMongoDb["dl303/tc"]
dbDl303RH = myMongoDb["dl303/rh"]
dbDl303CO2 = myMongoDb["dl303/co2"]
dbDl303DC = myMongoDb["dl303/dc"]
dbEt7044 = myMongoDb["et7044"]
dbUps = myMongoDb["ups"]
dbAirCondiction = myMongoDb["air_condiction"]
dbAirCondictionCurrent = myMongoDb["air_condiction_current"]
dbPowerBox = myMongoDb["power_box"]
dbDailyReport = myMongoDb["dailyReport"]
dbServiceCheck = myMongoDb["serviceCheck"]
dbServiceList = myMongoDb["serviceList"]
dbRotationUser = myMongoDb["rotationUser"]

settingMode = 0
settingObject = ""

# 懶人遙控器鍵盤定義
device_list = ['溫度', '濕度', 'CO2', '電流', 'DL303', 'ET7044', 'UPS', '冷氣', '環控設備' ,'遠端控制', '每日通報', '服務列表', '服務狀態', '機房輪值', '設定機房\n設備數量', '機房資訊']

# 設定機房資訊定義
setting_list = ['vCPU (Core)', 'RAM (GB)', 'Storage (TB)', 'General Switch', 'SDN Switch', 'x86_PC', 'Server Board', 'GPU Card', '離開設定狀態']
setting_json_list = ['cpu', 'ram', 'storage', 'switch', 'sdn', 'pc', 'gpu']
setting_unit_list = ['Core', 'GB', 'TB', '台', '台', '台', '台', '台']

# collect the the day of matainer in mLab db.
def getRotationUser():
    data = ""
    rotationUser = dbRotationUser.find_one()
    todayWeekDay = (datetime.datetime.now() + datetime.timedelta(hours=8)).weekday()
    tomorrowWeekDay = (datetime.datetime.now() + datetime.timedelta(hours=8, days=1)).weekday()
    if (rotationUser != None):
        data += "*[本日輪值人員公告]*\n"
        data += "[[今日輪值人員]]\n"
        for x in range(0, len(rotationUser["rotation"][todayWeekDay]["user"])):
            data += rotationUser["rotation"][todayWeekDay]["user"][x]
            if (x != len(rotationUser["rotation"][todayWeekDay]["user"]) - 1): data += ", "
            else:
                data += "\n"

        data += "[[今日交接人員]]\n"
        for x in range(0, len(rotationUser["rotation"][tomorrowWeekDay]["user"])):
            data += rotationUser["rotation"][tomorrowWeekDay]["user"][x]
            if (x != len(rotationUser["rotation"][tomorrowWeekDay]["user"]) - 1): data += ", "
            else:
                data += "\n"
    else:
        data = "`資料庫快取失敗`"
    return data

# collect the smart-data-center website url & login info in mLab db.
def getServiceList():
    broken = 0
    tagOwner = 0
    serviceList = dbServiceList.find_one()
    brokenTime = str(datetime.datetime.now()).split(" ")[0]
    if (serviceList != None):
        if (str(serviceList["date"]).split(" ")[0] == str(brokenTime)):
            if ("輪播 Dashboard" not in serviceList["error"]):
                data = serviceList
            else:
                data = "`輪播 DashBoard 資料快取失敗`"
        else:
            broken = 1
    else:
        broken = 1

    if (broken == 1):
        data = "`資料庫快取失敗`"
    return data

# collect the smart-data-center website dashboard service status in mLab db.
def getServiceCheck():
    broken = 0
    tagOwner = 0
    serviceStatus = dbServiceCheck.find_one()
    brokenTime = str(datetime.datetime.now() + datetime.timedelta(minutes=-3))
    if (serviceStatus != None):
        if (str(serviceStatus["date"]) > str(brokenTime)):
            data = "*[機房交接服務檢測]*\n"
            if ("輪播 Dashboard" not in serviceStatus["error"]):
                for x in range(0, len(serviceStatus["service"])):
                    data += "[[" + serviceStatus["service"][x]["name"] + "]]\n"
                    data += "`服務輪播: " + str(serviceStatus["service"][x]["enabled"]) + "`\n"
                    data += "`服務狀態: " + serviceStatus["service"][x]["status"] + "`\n"
                    data += "\n"
                    if (serviceStatus["service"][x]["status"] == "異常"): tagOwner = 1
            else:
                data += "`輪播 DashBoard 資料快取失敗`\n"
                tagOwner = 1
        else:
            broken = 1
    else:
        broken = 1

    if (broken == 1):
        data = "*[機房交接服務檢測]*\n"
        data += "`資料快取失敗`\n"
        tagOwner = 1

    if (tagOwner == 1):
        data += "----------------------------------\n"
        data += "*[交接服務檢測資料異常!]*\t"
        if (broken != 1): data += "*異常服務:* _" + str(checkService["error"]) + "_\n"
    return data

# collect the daily report data (weather / power usage) in mLab db.
def getDailyReport():
    broken = 0
    tagOwner = 0
    dailyReport = dbDailyReport.find_one()
    brokenTime = str(datetime.datetime.now()).split(" ")[0]
    if (dailyReport != None):
        if (str(dailyReport["date"]) == str(brokenTime)):
            data = "*[機房監控每日通報]*\n"
            data += "[[今日天氣預測]]\n"
            if ("weather" in dailyReport["error"]): 
                data += "`快取失敗`\n"
            else:
                data += "`天氣狀態:\t{0:s}`\n".format(dailyReport["Wx"])
                data += "`舒適指數:\t{0:s}`\n".format(dailyReport["CI"])
                data += "`降雨機率:{0:>5d} %`\n".format(int(dailyReport["PoP12h"]))
                data += "`陣風風向:\t{0:s}`\n".format(dailyReport["WD"])
                data += "`平均風速:{0:>5d} 公尺/秒`\n".format(int(dailyReport["WS"]))
                data += "`室外溫度:{0:>5.1f} 度`\n".format(int(dailyReport["T"]))
                data += "`體感溫度:{0:>5.1f} 度`\n".format(int(dailyReport["AT"]))
                data += "`室外濕度:{0:>5d} %`\n".format(int(dailyReport["RH"]))
            data += "[[昨日功耗統計]]\n"
            if ("power" in dailyReport["error"]): 
                data += "`快取失敗`\n"
            else:
                data += "`冷氣_A 功耗: {0:>6.2f} 度 ({1:>4.1f}%)`\n".format(float(dailyReport["air_condiction_a"]), float(float(dailyReport["air_condiction_a"])/float(dailyReport["total"])*100.0))
                data += "`冷氣_B 功耗: {0:>6.2f} 度 ({1:>4.1f}%)`\n".format(float(dailyReport["air_condiction_b"]), float(float(dailyReport["air_condiction_b"])/float(dailyReport["total"])*100.0))
                data += "`UPS_A 功耗: {0:>6.2f} 度 ({1:>4.1f}%)`\n".format(float(dailyReport["ups_a"]), float(float(dailyReport["ups_a"])/float(dailyReport["total"])*100.0))
                data += "`UPS_B 功耗: {0:>6.2f} 度 ({1:>4.1f}%)`\n".format(float(dailyReport["ups_b"]), float(float(dailyReport["ups_b"])/float(dailyReport["total"])*100.0))
                data += "`水塔功耗(預估): {0:>6.2f} 度 ({1:>4.1f}%)`\n".format(float(dailyReport["water_cooler"]), float(float(dailyReport["water_cooler"])/float(dailyReport["total"])*100.0))
                data += "`機房功耗加總: {0:>6.2f} 度`\n".format(float(dailyReport["total"]))
            if (len(dailyReport["error"]) > 0): tagOwner = 1
        else:
            broken = 1
    else:
        broken = 1

    if (broken == 1):
        data = "*[機房監控每日通報]*\n"
        data += "[[今日天氣預測]]\n"
        data += "`資料快取失敗`\n"
        data += "[[昨日功耗統計]]\n"
        data += "`資料快取失敗`\n"
        tagOwner = 1

    if (tagOwner == 1):
        data += "----------------------------------\n"
        data += "*[每日通報資料異常!]*\t"
        data += "[維護人員](tg://user?id="+ str(devUser_id) + ")\n"
        if (broken != 1): data += "*異常模組:* _" + str(dailyReport["error"]) + "_\n"
    return data
        
# test api function, can test the ("message", "photo", "audio", "gif") reply to develope user.
@app.route('/test/<mode>', methods=['GET'])
def test(mode):
    if (mode == 'message'): bot.send_message(chat_id=devUser_id, text="telegramBot 服務測試訊息")
    if (mode == 'localPhoto'): bot.sendPhoto(chat_id=devUser_id, photo=open('./test.png', 'rb'))
    if (mode == 'onlinePhoto'): bot.sendPhoto(chat_id=devUser_id, photo='https://i.imgur.com/ajMBl1b.jpg')
    if (mode == 'localAudio'): bot.sendAudio(chat_id=devUser_id, audio=open('./test.mp3', 'rb'))
    if (mode == 'onlineAudio'): bot.sendPhoto(chat_id=devUser_id, audio='http://s80.youtaker.com/other/2015/10-6/mp31614001370a913212b795478095673a25cebc651a080.mp3')
    if (mode == 'onlineGif'): bot.sendAnimation(chat_id=1070358833, animation='http://d21p91le50s4xn.cloudfront.net/wp-content/uploads/2015/08/giphy.gif')
    if (mode == 'localGif'): bot.sendAnimation(chat_id=1070358833, animation=open('./test.gif', 'rb'))

# rotationUser api function, send smart-data-center maintainer in this day.
@app.route('/rotationUser', methods=['GET'])
def rotationUser_update():
    if request.method == 'GET':
        respText = getRotationUser()
        bot.send_message(chat_id=devUser_id, text=respText, reply_markup = ReplyKeyboardRemove(), parse_mode="Markdown")
        return {"rotationUser": "data_ok"}, status.HTTP_200_OK
    else:
        return {"rotationUser": "data_fail"}, status.HTTP_401_UNAUTHORIZED

# service check api function, check the smart-data-center website dashboard service.
@app.route('/serviceCheck', methods=['GET'])
def serviceCheck_update():
    if request.method == 'GET':
        respText = getServiceCheck()
        bot.send_message(chat_id=devUser_id, text=respText, parse_mode="Markdown")
        return {"serviceCheck": "data_ok"}, status.HTTP_200_OK
    else:
        return {"serviceCheck": "data_fail"}, status.HTTP_401_UNAUTHORIZED

# daily report api function, will notice the daily report to specify group or user.
@app.route('/dailyReport', methods=['GET'])
def dailyReport_update():
    if request.method == 'GET':
        respText = getDailyReport()
        bot.send_message(chat_id=devUser_id, text=respText, reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("功能列表", callback_data = "daily")]
            ]), parse_mode="Markdown")
        return {"dailyReport": "data_ok"}, status.HTTP_200_OK
    else:
        return {"dailyReport": "data_fail"}, status.HTTP_401_UNAUTHORIZED

# alert notification api, auto notice the notifaiction to telegram specify user / group.
@app.route('/alert/<model>', methods=['POST'])
def alert(model):
    if request.method == 'POST':
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

# telegram bot data reciver.
@app.route('/hook', methods=['POST'])
def webhook_handler():
    """Set route /hook with POST method will trigger this method."""
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        # Update dispatcher process that handler to process this message
        dispatcher.process_update(update)
    return 'ok'

# collect the dl303 data (temperature/humidity/co2/dew-point) in mLab db.
def getDl303(info):
    brokenTime = datetime.datetime.now() + datetime.timedelta(minutes=-3)
    failList = []
    data = "*[DL303"
    if (info == "all"): data += "設備狀態回報]"
    else: data += " 工業監測器]"
    data += "*\n"
    if (info == "tc" or info == "all" or info == "temp/humi"):
        tc = dbDl303TC.find_one()
        if (tc != None):
            if (tc['date'] < brokenTime): failList.append('tc')
            data += "`即時環境溫度: {0:>5.1f} 度`\n".format(float(tc['tc']))
        else:
            data += "`即時環境溫度: None 度`\n"
            failList.append('tc')
    if (info == "rh" or info == "all" or info == "temp/humi"):
        rh = dbDl303RH.find_one()
        if (rh != None):
            if (rh['date'] < brokenTime): failList.append('rh')
            data += "`即時環境濕度: {0:>5.1f} %`\n".format(float(rh['rh']))
        else:
            data += "`即時環境濕度: None %`\n"
            failList.append('rh')
    if (info == "co2" or info == "all"):
        co2 = dbDl303CO2.find_one()
        if (co2 != None):
            if (co2['date'] < brokenTime): failList.append('co2')
            data += "`二氧化碳濃度: {0:>5d} ppm`\n".format(int(co2['co2']))
        else:
            data += "`二氧化碳濃度: None ppm`\n"
            failList.append('co2')
    if (info == "dc" or info == "all"):
        dc = dbDl303DC.find_one()
        if (dc != None):
            if (dc['date'] < brokenTime): failList.append('dc')
            data += "`環境露點溫度: {0:>5.1f} 度`\n".format(float(dc['dc']))
        else:
            data += "`環境露點溫度: None 度`\n"
            failList.append('dc')
    if (len(failList) > 0): 
        data += "----------------------------------\n"
        data += "*[設備資料超時!]*\t"
        data += "[維護人員](tg://user?id="+ str(dl303_owner) + ")\n"
        data += "*異常模組:* _" + str(failList) + "_\n"
    return data

# collect the et-7044 status in mLab.
def getEt7044(info):
    data = ""
    tagOwner = 0
    brokenTime = datetime.datetime.now() + datetime.timedelta(minutes=-3)
    if (info == "all"): data += "*[ET7044 設備狀態回報]*\n"
    et7044 = dbEt7044.find_one()
    if (info == "sw0" or info == "all"):
        if (et7044 == None): sw0 = "未知"
        elif(et7044['sw0'] == True): sw0 = "開啟"
        else: sw0 = "關閉"
        data += "`進風扇 狀態:\t" + sw0 + "`\n" 
    if (info == "sw1" or info == "all"):
        if (et7044 == None): sw1 = "未知"
        elif(et7044['sw1'] == True): sw1 = "開啟"
        else: sw1 = "關閉"
        data += "`加濕器 狀態:\t" + sw1 + "`\n" 
    if (info == "sw2" or info == "all"):
        if (et7044 == None): sw2 = "未知"
        elif(et7044['sw2'] == True): sw2 = "開啟"
        else: sw2 = "關閉"
        data += "`排風扇 狀態:\t" + sw2 + "`\n"
    if (info == "sw3" or info == "all"):
        if (et7044 == None): sw3 = "未知"
        elif(et7044['sw3'] == True): sw3 = "開啟"
        else: sw3 = "關閉"
        data += "`開關 3 狀態:\t" + sw3 + "`\n"  
    if (info == "sw4" or info == "all"):
        if (et7044 == None): sw4 = "未知"
        elif(et7044['sw4'] == True): sw4 = "開啟"
        else: sw4 = "關閉"
        data += "`開關 4 狀態:\t" + sw4 + "`\n" 
    if (info == "sw5" or info == "all"):
        if (et7044 == None): sw5 = "未知"
        elif(et7044['sw5'] == True): sw5 = "開啟"
        else: sw5 = "關閉"
        data += "`開關 5 狀態:\t" + sw5 + "`\n" 
    if (info == "sw6" or info == "all"):
        if (et7044 == None): sw6 = "未知"
        elif(et7044['sw6'] == True): sw6 = "開啟"
        else: sw6 = "關閉"
        data += "`開關 6 狀態:\t" + sw6 + "`\n" 
    if (info == "sw7" or info == "all"):
        if (et7044 == None): sw7 = "未知"
        elif(et7044['sw7'] == True): sw7 = "開啟"
        else: sw7 = "關閉"
        data += "`開關 7 狀態:\t" + sw7 + "`\n"
    if (et7044 != None):
        if (et7044['date'] < brokenTime): tagOwner = 1
    else: 
        tagOwner = 1
    if (tagOwner == 1):
        data += "----------------------------------\n"
        data += "*[設備資料超時!]*\t"
        data += "[維護人員](tg://user?id="+ str(et7044_owner) + ")\n"
    return data

# collect the UPS (status/input/output/battery/temperature) status in mLab.
def getUps(device_id, info):
    brokenTime = datetime.datetime.now() + datetime.timedelta(minutes=-3)
    data = "*["
    if (info == "all"): data += "不斷電系統狀態回報-"
    data += "UPS_" + str(device_id).upper() + "]*\n"
    if (dbUps.find({"sequence": device_id}).count() != 0): upsInfo = dbUps.find({"sequence": device_id})[0]
    else: upsInfo = None
    if (upsInfo != None):
        if (not (info == 'temp' or info == 'current')): data += "`UPS 狀態: {0:s}`\n".format(upsInfo['output']['mode'])
        if (info == 'temp' or info == "all"): data += "`機箱內部溫度: {0:>d} 度`\n".format(int(upsInfo['temp']))
        if (info == "all"): data += "----------------------------------\n"
        if (info == "input" or info == "all"):
            data += "[[輸入狀態]] \n"
            data += "`頻率: {0:>5.1f} HZ\n`".format(float(upsInfo['input']['freq']))
            data += "`電壓: {0:>5.1f} V\n`".format(float(upsInfo['input']['volt']))
        if (info == "output" or info == "all"):
            data += "[[輸出狀態]] \n"
            data += "`頻率: {0:>5.1f} HZ\n`".format(float(upsInfo['output']['freq']))
            data += "`電壓: {0:>5.1f} V\n`".format(float(upsInfo['output']['volt']))
        if (info == "output" or info == "current" or info == "all"): data += "`電流: {0:>5.2f} A`\n".format(float(upsInfo['output']['amp']))
        if (info == "output" or info == "all"):
            data += "`瓦數: {0:>5.3f} kw\n`".format(float(upsInfo['output']['watt']))
            data += "`負載比例: {0:>2d} %\n`".format(int(upsInfo['output']['percent']))
        if (info == 'battery' or info == "all"):
            data += "[[電池狀態]] \n"
            data += "`電池狀態: {0:s}`\n".format(str(upsInfo['battery']['status']['status']))
            data += "`充電模式: {0:s}`\n".format(str(upsInfo['battery']['status']['chargeMode']).split('(')[1].split(')')[0])
            data += "`電池電壓: {0:>3d} V`\n".format(int(upsInfo['battery']['status']['volt']))
            data += "`剩餘比例: {0:>3d} %`\n".format(int(upsInfo['battery']['status']['remainPercent']))
            data += "`電池健康: {0:s}`\n".format(str(upsInfo['battery']['status']['health']))
            data += "`上次更換時間: {0:s}`\n".format(str(upsInfo['battery']['lastChange']['year']) + "/" + str(upsInfo['battery']['lastChange']['month']) + "/" + str(upsInfo['battery']['lastChange']['day']))
            data += "`下次更換時間: {0:s}`\n".format(str(upsInfo['battery']['nextChange']['year']) + "/" + str(upsInfo['battery']['nextChange']['month']) + "/" + str(upsInfo['battery']['nextChange']['day']))
        if (upsInfo['date'] < brokenTime):
            data += "----------------------------------\n"
            data += "*[設備資料超時!]*\t"
            data += "[維護人員](tg://user?id="+ str(ups_owner) + ")\n"
    else:
        data += "`UPS 狀態: 未知`\n"
        data += "`機箱內部溫度: None 度`\n"
        if (info == "all"): data += "----------------------------------\n"
        if (info == "input" or info == "all"):
            data += "[[輸入狀態]] \n"
            data += "`頻率: None HZ\n`"
            data += "`電壓: None V\n`"
        if (info == "output" or info == "all"):
            data += "[[輸出狀態]] \n"
            data += "`頻率: None HZ\n`"
            data += "`電壓: None V\n`"
        if (info == "output" or info == "current" or info == "all"): data += "`電流: None A`\n"
        if (info == "output" or info == "all"):
            data += "`瓦數: None kw\n`"
            data += "`負載比例: None %\n`"
        if (info == 'battery' or info == "all"):
            data += "[[電池狀態]] \n"
            data += "`電池狀態: 未知 `\n"
            data += "`充電模式: 未知 `\n"
            data += "`電池電壓: None V`\n"
            data += "`剩餘比例: None %`\n"
            data += "`電池健康: 未知 `\n"
            data += "`上次更換時間: 未知 `\n"
            data += "`下次更換時間: 未知 `\n"
        data += "----------------------------------\n"
        data += "*[設備資料超時!]*\t"
        data += "[維護人員](tg://user?id="+ str(ups_owner) + ")\n"
    return data

# collect the Air-Condiction (current/temperature/humidity) status in mLab.
def getAirCondiction(device_id, info):
    brokenTime = datetime.datetime.now() + datetime.timedelta(minutes=-3)
    failList = []
    data = "*["
    if (info == "all"): data += "冷氣監控狀態回報-"
    data += "冷氣" + str(device_id).upper() + "]*\n"
    if (dbAirCondiction.find({"sequence": device_id}).count() != 0): envoriment = dbAirCondiction.find({"sequence": device_id})[0]
    else: envoriment = None
    if (dbAirCondictionCurrent.find({"sequence": device_id}).count() != 0): current = dbAirCondictionCurrent.find({"sequence": device_id})[0]
    else: current = None
    if (info == "temp" or info == "all" or info == "temp/humi"):
        if (envoriment != None): data += "`出風口溫度: {0:>5.1f} 度`\n".format(float(envoriment['temp']))
        else: data += "`出風口溫度: None 度`\n"
    if (info == "humi" or info == "all" or info == "temp/humi"):
        if (envoriment != None): data += "`出風口濕度: {0:>5.1f} %`\n".format(float(envoriment['humi']))
        else: data += "`出風口濕度: None %`\n"
    if (info == "humi" or info == "temp" or info == "all" or info == "temp/humi"):
        if (envoriment != None):
            if (envoriment['date'] < brokenTime): failList.append('temp/humi')
        else: 
            failList.append('temp/humi')
    if (info == "current" or info == "all"): 
        if (current != None): 
            data += "`冷氣耗電流: {0:>5.1f} A`\n".format(float(current['current']))
            if (current['date'] < brokenTime): failList.append('current')
        else:
            data += "`冷氣耗電流: None A`\n"
            failList.append('current')
    if (len(failList) > 0): 
        data += "----------------------------------\n"
        data += "*[設備資料超時!]*\t"
        data += "[維護人員](tg://user?id="+ str(air_condiction_owner) + ")\n"
        data += "*異常模組:* _" + str(failList) + "_\n"
    return data  

# recive the all of the user/group message handler.
def reply_handler(bot, update):
    global settingMode, settingObject
    """Reply message."""
    # print(dir(bot))
    # print(dir(update))
    # print(dir(update.message))
    # print(update.message.chat)
    # print(update.message.chat_id)
    # for s in device_list: print(s)
    text = update.message.text
    respText = ""

    if (settingMode == 1 and update.message.chat_id == devUser_id or update.message.chat_id == group_id):
        if (text in setting_list[:-1]):
            settingObject = text
            respText = "`請輸入" + settingObject + "數量~`"
        elif (text in setting_list[-1]):
            respText = "`您已離開機房資訊設定模式~`"
            settingMode = 0
            bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = ReplyKeyboardRemove(remove_keyboard=True), parse_mode="Markdown")
            return
        elif (settingObject != ""):
            print(text)
            try:
                if (settingObject == "Storage (TB)"):
                    float(text)
                else:
                    int(text)
                respText += "*[請確認機房設備數量]*"
                respText += "`設定項目:\t" + settingObject + "`\n"
                respText += "`設定數量:\t" + text + setting_unit_list[setting_list.index(settingObject)] + "`"
                print(respText)
                bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton('正確', callback_data = "setting:" + settingObject + "_" + text), 
                        InlineKeyboardButton('錯誤', callback_data = "setting:" + settingObject)
                    ]
                ]), parse_mode="Markdown")
                return
            except:
                respText = settingObject + '\t數值輸入錯誤～, 請重新輸入！'
        else:
            respText = '機房資訊設定中, 若需查詢其他服務, 請先關閉設定模式。'

    # 開啟 懶人遙控器鍵盤
    if (text == '輔助鍵盤'):
        respText = '輔助鍵盤功能已開啟～'
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = ReplyKeyboardMarkup([
            [str(s) for s in device_list[0:4]],
            [str(s) for s in device_list[4:8]],
            [str(s) for s in device_list[8:12]],
            [str(s) for s in device_list[12:16]]
        ], resize_keyboard=True), parse_mode="Markdown")
        bot.sendPhoto(chat_id=update.message.chat_id, photo=open('./keyboard.jpg', 'rb'))
        return

    
    #   關閉 懶人遙控器鍵盤
    if (text == '關閉鍵盤'):
        respText = '輔助鍵盤功能已關閉～'
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = ReplyKeyboardRemove(remove_keyboard=True), parse_mode="Markdown")
        return

    # 所有設備
    if (text == '環控設備'): 
        respText = '請選擇 監測設備～'
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('DL303 工業監測器', callback_data = "device:" + "DL303")],
            [InlineKeyboardButton('ET7044 工業控制器', callback_data = "device:" + "ET7044")],
            [InlineKeyboardButton('冷氣空調主機_A', callback_data = "device:" + "冷氣_A")],
            [InlineKeyboardButton('冷氣空調主機_B', callback_data = "device:" + "冷氣_B")],
            [InlineKeyboardButton('UPS不斷電系統_A', callback_data = "device:" + "UPS_B")],
            [InlineKeyboardButton('UPS不斷電系統_B', callback_data = "device:" + "UPS_B")],
            [InlineKeyboardButton('全部列出', callback_data = "device:" + "全部列出")]
        ]), parse_mode="Markdown")
        return

    # DL303 + 環境監測 回復
    if (text in ['DL303', 'dl303']): respText = getDl303("all")
    if (text == '溫度'): 
        respText = '請選擇 監測節點～'
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('DL303 工業監測器', callback_data = "temp:" + "DL303")],
            [InlineKeyboardButton('冷氣_A 出風口', callback_data = "temp:" + "冷氣_A")],
            [InlineKeyboardButton('冷氣_B 出風口', callback_data = "temp:" + "冷氣_B")],
            [InlineKeyboardButton('UPS_A 機箱內部', callback_data = "temp:" + "UPS_B")],
            [InlineKeyboardButton('UPS_B 機箱內部', callback_data = "temp:" + "UPS_B")],
            [InlineKeyboardButton('全部列出', callback_data = "temp:" + "全部列出")]
        ]), parse_mode="Markdown")
        return
        
    if (text == '濕度'): 
        respText = '請選擇 監測節點～'
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('DL303 工業監測器', callback_data = "humi:" + "DL303")],
            [InlineKeyboardButton('冷氣_A 出風口', callback_data = "humi:" + "冷氣_A")],
            [InlineKeyboardButton('冷氣_B 出風口', callback_data = "humi:" + "冷氣_B")],
            [InlineKeyboardButton('全部列出', callback_data = "humi:" + "全部列出")]
        ]), parse_mode="Markdown")
        return
        
    if (text == '溫濕度'): respText = getDl303("temp/humi") + "\n" + getAirCondiction("a", "temp/humi") + "\n" + getAirCondiction("b", "temp/humi") + "\n" + getUps("a", "temp") + "\n" + getUps("b", "temp")
    if (text == '露點溫度'): respText = getDl303("dc")
    if (text == 'CO2'): respText = getDl303("co2")

    # ET7044 狀態 回復
    if (text == 'ET7044' or text == 'et7044'): respText = getEt7044("all")
    if (text == '進風扇狀態'): respText = getEt7044("sw0")
    if (text == '加濕器狀態'): respText = getEt7044("sw1")
    if (text == '排風扇狀態'): respText = getEt7044("sw2")

    # Power Meter + UPS 電流 回覆
    if (text == '電流'): 
        respText = '請選擇 監測節點～'
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('冷氣空調主機_A', callback_data = "current:" + "冷氣_A")],
            [InlineKeyboardButton('冷氣空調主機_B', callback_data = "current:" + "冷氣_B")],
            [InlineKeyboardButton('UPS不斷電系統_A', callback_data = "current:" + "UPS_B")],
            [InlineKeyboardButton('UPS不斷電系統_B', callback_data = "current:" + "UPS_B")],
            [InlineKeyboardButton('全部列出', callback_data = "current:" + "全部列出")]
        ]), parse_mode="Markdown")
        return
        respText = getAirCondiction("a", "current") + "\n" + getAirCondiction("b", "current") + "\n" + getUps("a", "current") + "\n" + getUps("b", "current")
    
    # UPS 功能 回覆
    if (text in ['UPS狀態', 'ups狀態', 'UPS', 'ups', "電源狀態", 'Ups']):
        respText = '請選擇 UPS～'
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('UPS_A', callback_data = "UPS:" + "UPS_A")],
            [InlineKeyboardButton('UPS_B', callback_data = "UPS:" + "UPS_B")],
            [InlineKeyboardButton('全部列出', callback_data = "UPS:" + "全部列出")]
        ]), parse_mode="Markdown")
        return
    if (text in ['UPS_A', 'UPSA狀態', 'upsa狀態', 'UPSA', 'upsa', 'UpsA', 'Upsa']): respText = getUps("a", "all")
    if (text in ['UPS_B', 'UPSB狀態', 'upsb狀態', 'UPSB', 'upsb', 'UpsB', 'Upsb']): respText = getUps("b", "all")
    
    # 冷氣功能 回覆
    if (text == '冷氣狀態' or text == '冷氣'): 
        respText = '請選擇 冷氣～'
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('冷氣_A', callback_data = "冷氣:" + "冷氣_A")],
            [InlineKeyboardButton('冷氣_B', callback_data = "冷氣:" + "冷氣_B")],
            [InlineKeyboardButton('全部列出', callback_data = "冷氣:" + "全部列出")]
        ]), parse_mode="Markdown")
        return
    if (text in ['冷氣_A', '冷氣_a', '冷氣A狀態', '冷氣a狀態', '冷氣a', '冷氣A']): respText = getAirCondiction("a", "all")
    if (text in ['冷氣_B', '冷氣_b', '冷氣B狀態', '冷氣b狀態', '冷氣b', '冷氣B']): respText = getAirCondiction("b", "all")

    # 私密指令處理, 僅限制目前機房管理群 & 開發者使用
    if (text in ["遠端控制", "機房輪值", "輪值", "服務列表", "設定機房\n設備數量", "機房資訊"] and update.message.chat_id == devUser_id or update.message.chat_id == group_id):
        # 遠端控制
        if (text == '遠端控制'): 
            respText = '請選擇所需控制設備～'
            bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton('進風風扇', callback_data = "控制:" + "進風風扇")],
                [InlineKeyboardButton('加濕器', callback_data = "控制:" + "加濕器")],
                [InlineKeyboardButton('排風風扇', callback_data = "控制:" + "排風風扇")]
            ]), parse_mode="Markdown")
            return
        # 機房 Dashboard 服務列表
        if (text == '服務列表'):
            respText = "*[機房服務列表]*\n"
            try:
                serviceList = getServiceList()["service"]
                for x in range(0, len(serviceList)):
                    if (serviceList[x].get("user") != None and serviceList[x].get("pass") != None):
                        respText += "[[" + serviceList[x]["name"] + "]]\n"
                        respText += "帳號:" + serviceList[x]["user"] + "\n"
                        respText += "密碼:" + serviceList[x]["pass"] + "\n"
                        respText += "\n"
                bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(serviceList[x]["name"], callback_data = "service" + serviceList[x]["name"], url=serviceList[x]["url"])] for x in range(0, len(serviceList))
                ]), parse_mode="Markdown")
                return
            except:
                respText += getServiceList()
        
        # 每日通報
        if (text == "機房輪值" or text == "輪值"): respText = getRotationUser()

        # 設定機房資訊
        if (text == "設定機房\n設備數量"):
            respText = '設定機房資訊 模式開啟～'
            settingMode = 1
            bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = ReplyKeyboardMarkup([
                [str(s) for s in setting_list[0:3]],
                [str(s) for s in setting_list[3:6]],
                [str(s) for s in setting_list[6:9]]
            ], resize_keyboard=True), parse_mode="Markdown")
            bot.sendPhoto(chat_id=update.message.chat_id, photo=open('./keyboard.jpg', 'rb'))
            return

    
    elif (text in ["遠端控制", "機房輪值", "輪值", "服務列表", "設定機房\n設備數量", "機房資訊"]): 
        respText = '您的權限不足～, 請在機器人群組內使用。'
        bot.send_message(chat_id=update.message.chat_id, text=respText, parse_mode="Markdown")
        return
    
    if (text == '每日通報'): 
        respText = getDailyReport()
        bot.send_message(chat_id=update.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("功能列表", callback_data = "daily")]
            ]), parse_mode="Markdown")
        return

    # 機房 Dashboard 服務檢測 回覆            
    if (text in ['服務狀態', '服務檢測']): respText = getServiceCheck()

    #    print(dir(update.message))
    if (respText != ""): 
    #    update.message.reply_text(respText)
        bot.send_message(chat_id=update.message.chat_id, text=respText, parse_mode="Markdown")
        # update.message.reply_markdown(respText)

# Command "/satrt" callback. 
def addBot(bot, update):
    respText = "*[歡迎加入 NUTC-IMAC 機房監控機器人]*"
    respText += "[[快速使用]]\t`請輸入 \"輔助鍵盤\"。`\n"
    respText += "[[進階指令]]\t`請輸入 \"/command\"。`"
    bot.send_message(chat_id=update.message.chat_id, text=respText, parse_mode="Markdown")

# Command "/command" callback. 
def listCommand(bot, update):
    respText = "*[輔助指令列表]*\n"
    respText += "`命名規則: A (靠牆) / B (靠窗)`\n"
    respText += "[[快速鍵盤]]\n"
    respText += "`1. 輔助鍵盤`\n"
    respText += "`2. 關閉鍵盤`\n"
    respText += "[[每日通報]]\n"
    respText += "`1. 每日通報`\n"
    respText += "[[機房輪值]]\n"
    respText += "`1. 機房輪值`\n"
    respText += "[[機房服務檢視]]\n"
    respText += "`1. 服務列表`\n"
    respText += "`2. 服務狀態、服務檢測`\n"
    respText += "[[所有環控設備]]\n"
    respText += "`1. 環控設備`\n"
    respText += "[[DL303 工業監測器]]\n"
    respText += "`1. DL303`\n"
    respText += "`1. 溫度、溫濕度、濕度、CO2、露點溫度`\n"
    respText += "[[ET7044 工業控制器]]\n"
    respText += "`1. ET7044`\n"
    respText += "`2. 遠端控制`\n"
    respText += "`3. 進風扇狀態、加濕器狀態、排風扇狀態`\n"
    respText += "[[冷氣 空調主機 (A/B)]]\n"
    respText += "`1. 冷氣、冷氣狀態`\n"
    respText += "`2. 電流、溫度、濕度、溫濕度`\n"
    respText += "`3. 冷氣_A、冷氣_a、冷氣A、冷氣a`\n"
    respText += "`4. 冷氣a狀態、冷氣A狀態`\n"
    respText += "[[機房 瞬間功耗電流]]\n"
    respText += "`1. 電流`\n"
    respText += "[[UPS 不斷電系統 (A/B)]]\n"
    respText += "`1. 溫度、電流`\n"
    respText += "`2. UPS、Ups、ups`\n"
    respText += "`3. 電源狀態、UPS狀態、ups狀態`\n"
    respText += "`4. UPSA、upsa、UpsA、Upsa`\n"
    respText += "`5. UPS_A、UPSA狀態、upsa狀態`\n"
    bot.send_message(chat_id=update.message.chat_id, text=respText, parse_mode="Markdown")

# 每日通報 按鈕鍵盤 callback
def daily_select(bot, update):
    respText = '輔助鍵盤功能已開啟～'
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, reply_markup = ReplyKeyboardMarkup([
        [str(s) for s in device_list[0:4]],
        [str(s) for s in device_list[4:8]],
        [str(s) for s in device_list[8:12]],
        [str(s) for s in device_list[12:16]],
    ], resize_keyboard=True), parse_mode="Markdown")
    bot.sendPhoto(chat_id=update.callback_query.message.chat_id, photo=open('./keyboard.jpg', 'rb'))
    return

# 環控裝置 按鈕鍵盤 callback
def device_select(bot, update):
    device = update.callback_query.data.split(':')[1]
    if (device == "DL303"): respText = getDl303("all")
    elif (device == "ET7044"): respText = getEt7044("all")
    elif (device == "冷氣_A"): respText = getAirCondiction("a", "all")
    elif (device == "冷氣_B"): respText = getAirCondiction("b", "all")
    elif (device == "UPS_A"): respText = getUps("a", "all")
    elif (device == "UPS_B"): respText = getUps("b", "all")
    else: respText = getDl303("all") + '\n' + getEt7044("all") + '\n' + getAirCondiction("a", "all") + '\n' + getAirCondiction("b", "all") + '\n' + getUps("a", "all") + '\n' + getUps("b", "all")
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")

# 溫度 按鈕鍵盤 callback
def temp_select(bot, update):
    device = update.callback_query.data.split(':')[1]
    if (device == "DL303"): respText = getDl303("tc")
    elif (device == "冷氣_A"): respText = getAirCondiction("a", "temp")
    elif (device == "冷氣_B"): respText = getAirCondiction("b", "temp")
    elif (device == "UPS_A"): respText = getUps("a", "temp")
    elif (device == "UPS_B"): respText = getUps("b", "temp")
    else: respText = getDl303("tc") + "\n" + getAirCondiction("a", "temp") + "\n" + getAirCondiction("b", "temp") + "\n" + getUps("a", "temp") + "\n" + getUps("b", "temp")
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")

# 濕度 按鈕鍵盤 callback
def humi_select(bot, update):
    device = update.callback_query.data.split(':')[1]
    if (device == "DL303"): respText = getDl303("rh")
    elif (device == "冷氣_A"): respText = getAirCondiction("a", "humi")
    elif (device == "冷氣_B"): respText = getAirCondiction("b", "humi")
    else: respText = getDl303("rh") + "\n" + getAirCondiction("a", "humi") + "\n" + getAirCondiction("b", "humi")
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")

# 電流 按鈕鍵盤 callback
def current_select(bot, update):
    device = update.callback_query.data.split(':')[1]
    if (device == "冷氣_A"): respText = getAirCondiction("a", "current")
    elif (device == "冷氣_B"): respText = getAirCondiction("b", "current")
    elif (device == "UPS_A"): respText = getUps("a", "current")
    elif (device == "UPS_B"): respText = getUps("b", "current")
    else: respText = getAirCondiction("a", "current") + "\n" + getAirCondiction("b", "current") + "\n" + getUps("a", "current") + "\n" + getUps("b", "current")
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")

# UPS 按鈕鍵盤 callback
def ups_select(bot, update):
    device = update.callback_query.data.split(':')[1]
    if (device == "UPS_A"): respText = getUps("a", "all")
    elif (device == "UPS_B"): respText = getUps("b", "all")
    else: respText = getUps("a", "all") + "\n" + getUps("b", "all")
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")

# 冷氣 按鈕鍵盤 callback
def air_condiction_select(bot, update):
    device = update.callback_query.data.split(':')[1]
    if (device == "冷氣_A"): respText = getAirCondiction("a", "all")
    elif (device == "冷氣_B"): respText = getAirCondiction("b", "all")
    else: respText = getAirCondiction("a", "all") + "\n" + getAirCondiction("b", "all")
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")

# ET-7044 (選設備) 按鈕鍵盤 callback
def et7044_select(bot, update):
    device = update.callback_query.data.split(':')[1]
    device_map = {"進風風扇": "sw0", "加濕器": "sw1", "排風風扇": "sw2"}
    respText = "*[" + device + " 狀態控制]*\n"
    respText += getEt7044(device_map[device])
    if (len(respText.split('維護')) == 1):
        bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("開啟", callback_data = "開關:" + device + "_開啟"), 
            InlineKeyboardButton("關閉", callback_data = "開關:" + device + "_關閉")],
        ]), parse_mode="Markdown")
    else:
        bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")
    return

# ET-7044 (開關) 按鈕鍵盤 callback
def et7044_control(bot, update):
    device = str(update.callback_query.data).split(':')[1].split('_')[0]
    status = str(update.callback_query.data).split(':')[1].split('_')[1]
    device_map = {"進風風扇": "sw0", "加濕器": "sw1", "排風風扇": "sw2"}
    respText = "*[" + device + " 狀態更新]*\n"
    respText += "`" + device + " 狀態: \t" + status + "`\n"
    if (status == "開啟"): chargeStatus = True
    else:  chargeStatus = False
    if (len(respText.split('維護')) == 1): 
        dbEt7044.update_one({}, {'$set': {device_map[device]: chargeStatus}})
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")
    return

#  機房資訊確認 按鈕鍵盤 callback
def device_setting(bot, update):
    device = str(update.callback_query.data).split(':')[0].split('_')[0]
    if (len(str(update.callback_query.data).split(':')[1].split('_')) == 2):
        count = str(update.callback_query.data).split(':')[1].split('_')[1]
        respText = device + "\t設定成功"
        print (setting_json_list[setting_list.index(device)])
    else:
        respText = device + "\t資料已重設"
    bot.send_message(chat_id=update.callback_query.message.chat_id, text=respText, parse_mode="Markdown")
    return

# New a dispatcher for bot
dispatcher = Dispatcher(bot, None)

# Add handler for handling message, there are many kinds of message. For this handler, it particular handle text
# message.

dispatcher.add_handler(CommandHandler('start', addBot))
dispatcher.add_handler(CommandHandler('command', listCommand))
dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))
dispatcher.add_handler(CallbackQueryHandler(et7044_select, pattern=r'控制'))
dispatcher.add_handler(CallbackQueryHandler(et7044_control, pattern=r'開關'))
dispatcher.add_handler(CallbackQueryHandler(air_condiction_select, pattern=r'冷氣'))
dispatcher.add_handler(CallbackQueryHandler(ups_select, pattern=r'UPS'))
dispatcher.add_handler(CallbackQueryHandler(device_select, pattern=r'device'))
dispatcher.add_handler(CallbackQueryHandler(temp_select, pattern=r'temp'))
dispatcher.add_handler(CallbackQueryHandler(humi_select, pattern=r'humi'))
dispatcher.add_handler(CallbackQueryHandler(current_select, pattern=r'current'))
dispatcher.add_handler(CallbackQueryHandler(daily_select, pattern=r'daily'))
dispatcher.add_handler(CallbackQueryHandler(device_setting, pattern=r'setting'))

if __name__ == "__main__":
    # Running server
    app.run(debug=True)
