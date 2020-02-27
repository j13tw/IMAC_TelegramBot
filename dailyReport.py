import datetime
import requests
import time
import configparser

preDay = 0
sendReport = 0

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

server = config['HEROKU']['SERVER']

while (True):
    timeJson = datetime.datetime.strftime(datetime.datetime.now(), '{"day":%d, "hour":%H}')
    if (int(timeJson["hour"]) == 8 and sendReport == 0):
        sendReport = 1
        requests.get(server + "/dailyReport")
        requests.get(server + "/dailyReport")

    if (timeJson["day"] != preDay):
        sendReport = 0
    time.slppe(15)
    