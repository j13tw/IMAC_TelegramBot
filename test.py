import requests
import json
import datetime

data = {}
data["service"] = json.loads(requests.get("http://10.0.0.140:30010/").text)["res"]
data["date"] = str(datetime.datetime.now() + datetime.timedelta(hours=8))

for x in range(0, len(data["service"])):
    try:
        print(data["service"][x]["name"], data["service"][x]["url"], data["service"][x]["enabled"])
        if (data["service"][x]["name"] != "Kubernetes Dashboard"): r = requests.get(data["service"][x]["url"])
        else: r = requests.get(data["service"][x]["url"], verify=False)
        if (r.status_code == 200): data["service"][x]["status"] = "正常"
        else: data["service"][x]["name"]["status"] = "異常"
        if (len(data["service"][x]) == 5): data["service"][x]["notice"] = ""
        if (data["service"][x]["notice"].find("帳") >= 0 and data["service"][x]["notice"].find("密") >= 0):
            data["service"][x]["user"] = data["service"][x]["notice"].split("帳")[1].split(" ")[0]
            data["service"][x]["pass"] = data["service"][x]["notice"].split("密")[1]
    except:
        data["service"][x]["status"] = "異常"
print(str(data).replace("\'", '\"'))
