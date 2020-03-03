
data = {}
data["rotation"] = []
for x in range(1, 8):
    weekDay = ""
    if (x == 1): weekDay = "一"
    elif (x == 2): weekDay = "二"
    elif (x == 3): weekDay = "三"
    elif (x == 4): weekDay = "四"
    elif (x == 5): weekDay = "五"
    elif (x == 6): weekDay = "六"
    else: (x == 7): weekDay = "日"
    data["rotation"].append({})
    data["rotation"][int(x)]["user"] = []
    data["rotation"][int(x)]["user"].append("星期" + "_人員_0")
    data["rotation"][int(x)]["user"].append("星期" + "_人員_1")
print(str(data).replace("\'", "\""))