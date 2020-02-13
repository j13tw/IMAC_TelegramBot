import paho.mqtt.subscribe as subscribe
import requests
import datetime

broker_ip = "10.20.0.19"
broker_port = 1883

http_server_protocol = "http"
#http_server_ip = "10.20.0.74"
http_server_ip = "127.0.0.1"
http_server_port = 5000

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    
    client.subscribe("DL303/TC")
    client.subscribe("DL303/CO2")
    client.subscribe("DL303/RH")
    client.subscribe("DL303/DC")
    #client.subscribe("ET7044/DOstatus")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    sendData = {}
    data = str(msg.payload.decode('utf-8'))
    if (msg.topic == "DL303/TC"):
        sendData["tc"] = data
        try:
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/dl303/tc", json=sendData)
        except:
            pass
    if (msg.topic == "DL303/CO2"):
        sendData["co2"] = data
        print(sendData)
        try:
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/dl303/co2", json=sendData)
        except:
            pass
    if (msg.topic == "DL303/RH"):
        sendData["rh"] = data
        try:
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/dl303/rh", json=sendData)
        except:
            pass
    if (msg.topic == "DL303/DC"):
        sendData["dp"] = data
        try:
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/dl303/dp", json=sendData)
        except:
            pass
    if (msg.topic == "ET7044/DOstatus"):
        data = data.split("[")[1].split("]")[0].split(",")
        for x in range(0, len(data)):
            sendData["sw" + str(x)] = data[x].lower() in ['true']
        print(sendData)
        try:
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/et7044", json=sendData)
        except:
            pass
    print(msg.topic+" "+ data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_ip, broker_port)
client.loop_forever()