import datetime
import requests
import time
import json

preDay = 0
sendReport = 0

while (True):
    timeJson = json.loads(datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(hours=8), '{"day":%d, "hour":%H}'))
    if (int(timeJson["hour"]) == 8 and sendReport == 0):
        sendReport = 1
        try: 
            requests.get("http://127.0.0.1:5000/dailyReport")
        except: 
            pass
    if (timeJson["day"] != preDay): 
        preDay = timeJson["day"]
        sendReport = 0
    time.slppe(15)