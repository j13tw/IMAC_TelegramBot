import paho.mqtt.subscribe as subscribe
import requests

broker_ip = "10.20.0.19"
broker_port = 1883

http_server_ip = "10.20.0.74"
http_server_port = 5000

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("DL303/CO")
    client.subscribe("DL303/CO2")
    client.subscribe("DL303/RH")
    client.subscribe("DL303/DC")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    sendData = {}
    data = str(msg.payload.decode('utf-8'))
    if (msg.topic == "DL303/CO"):
        sendData["tc"] = data
        requests.post(http_server_ip + ":" + str(http_server_port), json=sendData)
    if (msg.topic == "DL303/CO2"):
        sendData["co2"] = data
        requests.post(http_server_ip + ":" + str(http_server_port), json=sendData)
    if (msg.topic == "DL303/RH"):
        sendData["rh"] = data
        requests.post(http_server_ip + ":" + str(http_server_port), json=sendData)
    if (msg.topic == "DL303/DC"):
        sendData["dp"] = data
        requests.post(http_server_ip + ":" + str(http_server_port), json=sendData)
    print(msg.topic+" "+ data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_ip, broker_port)
client.loop_forever()