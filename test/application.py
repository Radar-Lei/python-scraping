from urllib.parse import quote
from urllib import request as url_request
import string
import pandas as pd
import json
from sqlalchemy import create_engine
from flask import Flask, render_template
from flask import request as flask_request
import json
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv


baidu_web_key = 'k74dnzzNHEmOsCkzTCxVrKhEH62vcVYP'
poi_search_url = "http://api.map.baidu.com/place/v2/search"

radius = 500
queries = ['教育培训', '住宅区']

# 根据城市名称和分类关键字获取poi数据


def getpois(name_list, location, queries):
    poilist = pd.DataFrame(
        columns=['location', 'type', 'area', 'name', 'address'])
    for j in range(len(location)):
        loc = location[j]
        station_name = name_list[j].encode('utf_8-sig')
        station_name = station_name.decode('utf_8-sig')
        # engine = create_engine(
        # 'postgresql://username:password@database.cn:5432/postgres')
        for query in queries:
            i = 0
            # print(loc, query)
            while True:  # 使用while循环不断分页获取数据
                result = getpoi_page(loc, query, i)
                result = json.loads(result)  # 将字符串转换为json

                if len(result['results']) == 0:
                    break

                result = pd.DataFrame(result['results'])
                data1 = result[['area', 'name', 'address']]

                data2 = pd.DataFrame(
                    [[station_name, query]] * len(data1.index), columns=['location', 'type'])
                df = (pd.concat([data2, data1], axis=1))
                poilist = pd.concat([poilist, df], ignore_index=True)
                # df.to_sql('bd_pois', engine, schema='analyst',
                # index = False, if_exists = 'append')
                # df.to_csv('C:\\Users\\Felicity\\Desktop\\bd_pois.csv', mode='a', header=False, index=False, encoding='utf_8_sig')
                i = i + 1

    return poilist


def getpoi_page(loc, query, page):
    req_url = poi_search_url + "?query=" + query + "&location=" + \
        quote(loc) + '&offset=25' + '&radius=' + str(radius) + '&page_size=20' + \
        '&page_num=' + str(page) + '&output=json&ak=' + baidu_web_key
    r = quote(req_url, safe=string.printable)  # quote的参数表示可以忽略的字符
    # string.printable表示ASCII码第33～126号可打印字符，
    # 其中第48～57号为0～9十个阿拉伯数字；65～90号为26个大写英文字母，
    # 97～122号为26个小写英文字母，其余的是一些标点符号、运算符号等
    data = ''
    with url_request.urlopen(r) as f:
        data = f.read()
        data = data.decode('utf-8')
    return data


app = Flask(__name__)
pois = [0]

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("submit data")
def poi(data):
    location = data["location_list"]
    name_list = data["name_list"]
    pois = getpois(name_list, location, queries)
    pois.to_csv('bd_pois.csv',
                mode='a', header=False, index=False, encoding='utf_8-sig')
