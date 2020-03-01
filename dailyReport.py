import datetime
import requests
import time
import configparser
import json

preDay = 0
sendReport = 0

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

data = {}

while (True):
    timeJson = json.loads(datetime.datetime.strftime(datetime.datetime.now(), '{"date": "%Y-%m-%d" ,"day":%d, "hour":%H}'))
    if (int(timeJson["hour"]) == 0 and sendReport == 0):
        sendReport = 1
        try: 
            requests.get("http://127.0.0.1:5000/dailyReport")
        except: 
            pass
    if (timeJson["day"] != preDay): sendReport = 0
    time.slppe(15)
    