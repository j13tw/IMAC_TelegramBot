from flask import Flask, request
from flask_api import status
import json
from pymongo import MongoClient
import datetime
import configparser

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

# Initial Flask app
app = Flask(__name__)

# Setup Mongodb info
print(config['MONGODB']['SERVER_PROTOCOL'] + "://" + config['MONGODB']['USER'] + ":" + config['MONGODB']['PASSWORD'] + "@" + config['MONGODB']['SERVER'])
myMongoClient = MongoClient(config['MONGODB']['SERVER_PROTOCOL'] + "://" + config['MONGODB']['USER'] + ":" + config['MONGODB']['PASSWORD'] + "@" + config['MONGODB']['SERVER'])
myMongoDb = myMongoClient["smart-data-center"]
#myMongoDb.authenticate(config['MONGODB']['USER'], config['MONGODB']['PASSWORD'])
dbDl303TC = myMongoDb["dl303/tc"]
dbDl303RH = myMongoDb["dl303/rh"]
dbDl303CO2 = myMongoDb["dl303/co2"]
dbDl303DP = myMongoDb["dl303/dp"]
dbEt7044 = myMongoDb["et7044"]
dbUpsA = myMongoDb["ups_a"]
dbUpsB = myMongoDb["ups_b"]
dbAirCondiction = myMongoDb["air_condiction"]
dbAirCondictionCurrent = myMongoDb["air_condiction_current"]

@app.route('/air_condiction/<module>/<sequence>', methods=['POST'])
def air_condiction_update(module, sequence):
    if request.method == 'POST':
        print(module.lower(), sequence.lower(), request.json)
        if (not (module.lower() in ["envoriment", "current"])): return {"air-condiction": "api_module_fail"}, status.HTTP_401_UNAUTHORIZED 
        if (not (sequence.lower() in ["a", "b"])): return {"air-condiction": "api_sequence_fail"}, status.HTTP_401_UNAUTHORIZED
        try:
            data = request.json
            if (module == "envoriment"): 
                try:
                    data["humi"]
                    data["temp"]
                except:
                    return {"air-condiction-envoriment": "data_fail"}, status.HTTP_401_UNAUTHORIZED
            if (module == "current"):
                try:
                    data["current"]
                except:
                    return {"air-condiction-current": "data_fail"}, status.HTTP_401_UNAUTHORIZED
        except:
            return {"air-condiction": "data_fail"}, status.HTTP_401_UNAUTHORIZED
        data["sequence"] = sequence
        data["date"] = datetime.datetime.now()
        if (module == "envoriment"):
            if (dbAirCondiction.find_one({"sequence": sequence}) == None): dbAirCondiction.insert_one(data)
            else: dbAirCondiction.update_one({"sequence": sequence},{'$set':data})
            return {"ait-condiction-envoriment": "data_ok"}, status.HTTP_200_OK
        else:
            if (dbAirCondictionCurrent.find_one({"sequence": sequence}) == None): dbAirCondictionCurrent.insert_one(data)
            else: dbAirCondictionCurrent.update_one({"sequence": sequence},{'$set':data})
            return {"ait-condiction-current": "data_ok"}, status.HTTP_200_OK

@app.route('/ups/<sequence>', methods=['POST'])
def ups_update(sequence):
    if request.method == 'POST':
        if (not (sequence in ["A", "B"])): return {"ups": "api_sequence_fail"}, status.HTTP_401_UNAUTHORIZED
        try:
            data = json.loads(str(request.json).replace("'", '"'))
        except:
            return {"ups": "data_fail"}, status.HTTP_401_UNAUTHORIZED
        data["date"] = datetime.datetime.now()
        data["sequence"] = sequence
        if (dbUps.find_one() == None): dbUps.insert_one(data)
        else: dbUps.update_one({'sequence': sequence},{'$set':data})
        return {"ups": "data_ok"}, status.HTTP_200_OK

@app.route('/et7044', methods=['POST', 'GET'])
def et7044_update():
    if request.method == 'POST':
        try:
            data = request.json
            if (not ((data['sw0'] in [True, False]) and (data['sw1'] in [True, False]) and (data['sw2'] in [True, False]) and (data['sw3'] in [True, False]) and (data['sw4'] in [True, False]) and (data['sw5'] in [True, False]) and (data['sw6'] in [True, False]) and (data['sw7'] in [True, False]))):
                return {"et7044": "data_info_fail"}, status.HTTP_401_UNAUTHORIZED
            data["date"] = datetime.datetime.now()
            if (dbEt7044.find_one() == None): dbEt7044.insert_one(data)
            else: dbEt7044.update_one({'sw0': dbEt7044.find_one()['sw0']}, {'$set': data})
            return {"et7044": "data_ok"}, status.HTTP_200_OK
        except:
            return {"et7044": "data_fail"}, status.HTTP_401_UNAUTHORIZED
    else:
        data = dbEt7044.find_one()
        return {"sw0": data['sw0'], "sw2": data['sw2'], "sw3": data['sw3'], "sw4": data['sw4'], "sw5": data['sw5'], "sw": data['sw'], "sw6": data['sw6'], "sw7": data['sw7'], "date": datetime.datetime.now()}

@app.route('/dl303/<module>', methods=['POST'])
def dl303_update(module):
    if request.method == 'POST':
        if (not (module in ["tc", "rh", "co2", "dp"])): return {"dl303": "api_module_fail"}, status.HTTP_401_UNAUTHORIZED
        try: data = request.json
        except: return {"dl303": "data_fail"}, status.HTTP_401_UNAUTHORIZED
        if (module == 'tc'):
            try:
                data['tc']
                data["date"] = datetime.datetime.now()
                if (dbDl303TC.find_one() == None): dbDl303TC.insert_one(data)
                else: dbDl303TC.update_one({'tc': dbDl303TC.find_one()['tc']}, {'$set': data})
                return {"dl303": "tc_data_ok"}, status.HTTP_200_OK
            except:
                return {"dl303": "tc_data_info_fail"}, status.HTTP_401_UNAUTHORIZED
        elif (module == 'rh'):
            try:
                data['rh']
                data["date"] = datetime.datetime.now()
                if (dbDl303RH.find_one() == None): dbDl303RH.insert_one(data)
                else: dbDl303RH.update_one({'rh': dbDl303RH.find_one()['rh']}, {'$set': data})
                return {"dl303": "rh_data_ok"}, status.HTTP_200_OK
            except:
                return {"dl303": "rh_data_info_fail"}, status.HTTP_401_UNAUTHORIZED
        elif (module == 'co2'):
            try:
                data['co2']
                data["date"] = datetime.datetime.now()
                if (dbDl303CO2.find_one() == None): dbDl303CO2.insert_one(data)
                else: dbDl303CO2.update_one({'co2': dbDl303CO2.find_one()['co2']}, {'$set': data})
                return {"dl303": "co2_data_ok"}, status.HTTP_200_OK
            except:
                return {"dl303": "co2_data_info_fail"}, status.HTTP_401_UNAUTHORIZED
        elif (module == 'dp'):
            try:
                data['dp']
                data["date"] = datetime.datetime.now()
                if (dbDl303DP.find_one() == None): dbDl303DP.insert_one(data)
                else: dbDl303DP.update_one({'dp': dbDl303DP.find_one()['dp']}, {'$set': data})
                return {"dl303": "dp_data_ok"}, status.HTTP_200_OK
            except:
                return {"dl303": "dp_data_info_fail"}, status.HTTP_401_UNAUTHORIZED

if __name__ == "__main__":
    # Running server
    app.run(host="0.0.0.0")