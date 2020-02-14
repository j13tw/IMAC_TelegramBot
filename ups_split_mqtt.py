import paho.mqtt.subscribe as subscribe
import requests
import datetime
import json

broker_ip = "10.20.0.19"
broker_port = 1883

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # client.subscribe("UPS_Monitor/#")
    client.subscribe("UPS_Monitor")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    sendData = {}
    data = str(msg.payload.decode('utf-8'))
    if (msg.topic == "UPS_Monitor"):
        print(data)
        data = json.loads(data)
        ups_a_data = {}
        ups_b_data = {}
        ups_a_data["connect"] = data["connect_A"]
        ups_a_data["upsLife"] = data["ups_Life_A"]
        ups_a_data["input"] = {}
        ups_a_data["input"]["line"] = int(data["input_A"]["inputLine_A"])
        ups_a_data["input"]["freq"] = float(data["input_A"]["inputFreq_A"])
        ups_a_data["input"]["volt"] = float(data["input_A"]["inputVolt_A"])
        ups_a_data["output"] = {}
        ups_a_data["output"]["systemMode"] = data["output_A"]["systemMode_A"]
        ups_a_data["output"]["line"] = int(data["output_A"]["outputLine_A"])
        ups_a_data["output"]["freq"] = float(data["output_A"]["outputFreq_A"])
        ups_a_data["output"]["volt"] = float(data["output_A"]["outputVolt_A"])
        ups_a_data["output"]["amp"] = float(data["output_A"]["outputAmp_A"])
        ups_a_data["output"]["percent"] = int(data["output_A"]["outputPercent_A"])
        ups_a_data["output"]["watt"] = float(data["output_A"]["outputWatt_A"])
        ups_a_data["battery"] = {}
        ups_a_data["battery"]["status"] = {}
        ups_a_data["battery"]["lastChange"] = {}
        ups_a_data["battery"]["nextChange"] = {}
        ups_a_data["battery"]["status"]["health"] = data["battery_A"]["status"]["batteryHealth_A"]
        ups_a_data["battery"]["status"]["status"] = data["battery_A"]["status"]["batteryStatus_A"]
        ups_a_data["battery"]["status"]["chargeMode"] = data["battery_A"]["status"]["batteryCharge_Mode_A"]
        ups_a_data["battery"]["status"]["remain_Min"] = data["battery_A"]["status"]["batteryRemain_Min_A"]
        ups_a_data["battery"]["status"]["remain_Sec"] = data["battery_A"]["status"]["batteryRemain_Sec_A"]
        ups_a_data["battery"]["status"]["volt"] = float(data["battery_A"]["status"]["batteryVolt_A"])
        ups_a_data["battery"]["status"]["temp"] = float(data["battery_A"]["status"]["batteryTemp_A"])
        ups_a_data["battery"]["status"]["remainPercent"] = int(data["battery_A"]["status"]["batteryRemain_Percent_A"])
        ups_a_data["battery"]["lastChange"]["year"] = int(data["battery_A"]["lastChange"]["lastBattery_Year_A"])
        ups_a_data["battery"]["lastChange"]["month"] = int(data["battery_A"]["lastChange"]["lastBattery_Mon_A"])
        ups_a_data["battery"]["lastChange"]["day"] = int(data["battery_A"]["lastChange"]["lastBattery_Day_A"])
        ups_a_data["battery"]["nextChange"]["year"] = int(data["battery_A"]["nextChange"]["nextBattery_Year_A"])
        ups_a_data["battery"]["nextChange"]["month"] = int(data["battery_A"]["nextChange"]["nextBattery_Mon_A"])
        ups_a_data["battery"]["nextChange"]["day"] = int(data["battery_A"]["nextChange"]["nextBattery_Day_A"])
        print(ups_a_data)
        client.publish("UPS_Monitor/A", str(ups_a_data))
        ups_b_data["connect"] = data["connect_B"]
        ups_b_data["upsLife"] = data["ups_Life_B"]
        ups_b_data["input"] = {}
        ups_b_data["input"]["line"] = int(data["input_B"]["inputLine_B"])
        ups_b_data["input"]["freq"] = float(data["input_B"]["inputFreq_B"])
        ups_b_data["input"]["volt"] = float(data["input_B"]["inputVolt_B"])
        ups_b_data["output"] = {}
        ups_b_data["output"]["systemMode"] = data["output_B"]["systemMode_B"]
        ups_b_data["output"]["line"] = int(data["output_B"]["outputLine_B"])
        ups_b_data["output"]["freq"] = float(data["output_B"]["outputFreq_B"])
        ups_b_data["output"]["volt"] = float(data["output_B"]["outputVolt_B"])
        ups_b_data["output"]["amp"] = float(data["output_B"]["outputAmp_B"])
        ups_b_data["output"]["percent"] = int(data["output_B"]["outputPercent_B"])
        ups_b_data["output"]["watt"] = float(data["output_B"]["outputWatt_B"])
        ups_b_data["battery"] = {}
        ups_b_data["battery"]["status"] = {}
        ups_b_data["battery"]["lastChange"] = {}
        ups_b_data["battery"]["nextChange"] = {}
        ups_b_data["battery"]["status"]["health"] = data["battery_B"]["status"]["batteryHealth_B"]
        ups_b_data["battery"]["status"]["status"] = data["battery_B"]["status"]["batteryStatus_B"]
        ups_b_data["battery"]["status"]["chargeMode"] = data["battery_B"]["status"]["batteryCharge_Mode_B"]
        ups_b_data["battery"]["status"]["remain_Min"] = data["battery_B"]["status"]["batteryRemain_Min_B"]
        ups_b_data["battery"]["status"]["remain_Sec"] = data["battery_B"]["status"]["batteryRemain_Sec_B"]
        ups_b_data["battery"]["status"]["volt"] = float(data["battery_B"]["status"]["batteryVolt_B"])
        ups_b_data["battery"]["status"]["temp"] = float(data["battery_B"]["status"]["batteryTemp_B"])
        ups_b_data["battery"]["status"]["remainPercent"] = int(data["battery_B"]["status"]["batteryRemain_Percent_B"])
        ups_b_data["battery"]["lastChange"]["year"] = int(data["battery_B"]["lastChange"]["lastBattery_Year_B"])
        ups_b_data["battery"]["lastChange"]["month"] = int(data["battery_B"]["lastChange"]["lastBattery_Mon_B"])
        ups_b_data["battery"]["lastChange"]["day"] = int(data["battery_B"]["lastChange"]["lastBattery_Day_B"])
        ups_b_data["battery"]["nextChange"]["year"] = int(data["battery_B"]["nextChange"]["nextBattery_Year_B"])
        ups_b_data["battery"]["nextChange"]["month"] = int(data["battery_B"]["nextChange"]["nextBattery_Mon_B"])
        ups_b_data["battery"]["nextChange"]["day"] = int(data["battery_B"]["nextChange"]["nextBattery_Day_B"])
        print(ups_b_data)
        client.publish("UPS_Monitor/B", str(ups_b_data))
    print(msg.topic+" "+ data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_ip, broker_port)
client.loop_forever()