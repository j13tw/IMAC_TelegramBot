import paho.mqtt.subscribe as subscribe
import requests
import datetime
import json

broker_ip = "10.20.0.19"
broker_port = 1883

http_server_protocol = "http"
#http_server_ip = "10.20.0.74"
http_server_ip = "10.20.0.74"
http_server_port = 5000

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    
    client.subscribe("DL303/#")
    # client.subscribe("DL303/TC")
    # client.subscribe("DL303/CO2")
    # client.subscribe("DL303/RH")
    # client.subscribe("DL303/DC")
    client.subscribe("ET7044/DOstatus")
    client.subscribe("current")
    client.subscribe("UPS_Monitor/#")
    # client.subscribe("UPS_Monitor")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    sendData = {}
    data = str(msg.payload.decode('utf-8'))
    if (msg.topic in ["DL303/TC", "DL303/CO2", "DL303/RH", "DL303/DC"]):
        moduleName = msg.topic.lower().split("/")[1]
        try:
            sendData[moduleName] = data
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/dl303/" + moduleName, json=sendData)
        except:
            pass
    if (msg.topic == "ET7044/DOstatus"):
        data = data.split("[")[1].split("]")[0].split(",")
        for x in range(0, len(data)):
            sendData["sw" + str(x)] = data[x].lower() in ['true']
        #print(sendData)
        try:
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/et7044", json=sendData)
        except:
            pass
    if (msg.topic == "current"):
        print(data)
        data = json.loads(data)
        air_condiction_a = {}
        air_condiction_b = {}
        power_box = {}
        air_condiction_a['current'] = data['current_a']
        air_condiction_b['current'] = data['currents_b']
        power_box["temp"] = data["Temperature"]
        power_box["humi"] = data["Humidity"]
        try:
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/power_box", json=power_box)
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/air_condiction/current/a", json=air_condiction_a)
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/air_condiction/current/b", json=air_condiction_b)
        except:
            pass
    if (msg.topic in ["UPS_Monitor/A", "UPS_Monitor/B"]):
        try:
            moduleName = msg.topic.lower().split("/")[1]
            requests.post(http_server_protocol + "://" + http_server_ip + ":" + str(http_server_port) + "/ups/" + moduleName, json=json.loads(data.replace("'", '"')))
        except:
            pass
        print(data)
    print(msg.topic+" "+ data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_ip, broker_port)
client.loop_forever()