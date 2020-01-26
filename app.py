import configparser
import logging

import telegram
from flask import Flask, request
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import json

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

Test_A, Test_B = range(2)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initial Flask app
app = Flask(__name__)

# Initial bot by Telegram access token
bot = telegram.Bot(token=(config['TELEGRAM']['ACCESS_TOKEN']))


@app.route('/hook', methods=['POST'])
def webhook_handler():
    """Set route /hook with POST method will trigger this method."""
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        # Update dispatcher process that handler to process this message
        dispatcher.process_update(update)
    return 'ok'

def getDl303(info):
    if (info == "all"):
        return "dl303 = get_all"
    elif (info == "humi"):
        return "dl303 = get_humi"
    elif (info == "temp"):
        return "dl303 = get_temp"
    elif (info == "co2"):
        return "dl303 = get_c02"
    elif (info == "dp"):
        return "dl303 = get_dp"
    else:
        return "dl303 = fail"

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
    for s in device_list: print(s)
    text = update.message.text
    if (text == '資訊列表'): 
        text = '請選擇所需設備資訊～'
        update.message.reply_text(text, reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[0:2]],
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[2:4]],
            [InlineKeyboardButton(str(s), callback_data = '{\"device\": \"' + s + '\"}') for s in device_list[4:6]]
        ]))
    return 0
    if (text == '溫濕度'): text = '現在溫度: 25.8 度\n現在濕度: 50 %'
    if (text == '溫度'): text = '現在溫度: 25.8 度'
    if (text == '濕度'): text = '現在濕度: 50 %'
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

def device_test_a(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=u"First CallbackQueryHandler"
    )
    return

def device_test_b(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=u"Second CallbackQueryHandler"
    )
    return

# New a dispatcher for bot
dispatcher = Dispatcher(bot, None)

# Add handler for handling message, there are many kinds of message. For this handler, it particular handle text
# message.

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.text, reply_handler)],
    states={
        Test_A: [CallbackQueryHandler(device_test_a)],
        Test_B: [CallbackQueryHandler(device_test_b)]
    },
    fallbacks=[CommandHandler('start', start)]
)

dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))
dispatcher.add_handler(CallbackQueryHandler(device_select))
dispatcher.add_handler(conv_handler)

if __name__ == "__main__":
    # Running server
    app.run(debug=True)
