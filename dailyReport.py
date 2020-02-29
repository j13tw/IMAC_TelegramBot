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

defaultUrl = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-D0047-073"
apiToken = "CWB-011FFC7B-436E-4268-ABCA-998FBD6AD424"
locationName = "%E5%8C%97%E5%8D%80"
timeStamp_a = "T06%3A00%3A00"
timeStamp_b = "T06%3A00%3A00"

data = {}

while (True):
    timeJson = json.loads(datetime.datetime.strftime(datetime.datetime.now(), '{"date": "%Y-%m-%d" ,"day":%d, "hour":%H}'))
    if (int(timeJson["hour"]) == 8 and sendReport == 0):
        sendReport = 1
        try:
            requestUrl = defaultUrl + "?Authorization=" + apiToken + "&locationName=" + locationName + "&startTime=" + timeJson['date'] + timeStamp_a + "," + timeJson['date'] + timeStamp_b + "&dataTime=" + timeJson['date'] + timeStamp_b
            weatherJson = json.loads(requests.get(requestUrl, headers = {'accept': 'application/json'}))
            
            for x in range(0, len(weatherJson["records"]["locations"][0]["location"][0]["weatherElement"])):
                module = weatherJson["records"]["locations"][0]["location"][0]["weatherElement"][x]["elementName"]
                value = weatherJson["records"]["locations"][0]["location"][0]["weatherElement"][x]["time"][0]["elementValue"][0]["value"]
                print(module, value)
                data[module] = value
            
            requests.get(server + "/dailyReport")

    if (timeJson["day"] != preDay):
        sendReport = 0
    time.slppe(15)
    