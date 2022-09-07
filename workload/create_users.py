import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

URL = os.environ.get('TRAIN_TICKET_URL', 'http://127.0.0.1:32677')


def get_admin_token():
    url = "{URL}/api/v1/users/login".format(URL=URL)
    payload = "{\n    \"username\": \"admin\",\n    \"password\": \"222222\"\n}"
    headers = {
        'Content-Type': 'application/json;charset=utf-8',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Content-Length': '40',
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    try:
        token = response.json()['data']['token']
        print(f"admin token: {token=}")
        return token
    except:
        print("Get admin token failed, ", response.text)
        sys.exit(1)


TOKEN = get_admin_token()


def create_user(bot_id):
    url = "{URL}/api/v1/adminuserservice/users".format(URL=URL)
    print(bot_id, url)
    payload = "{\"userName\":\"bots-bot_id\",\"password\":\"bot\",\"gender\":\"0\",\"email\":\"bots-bot_id@train-ticket1.peidan.me\",\"documentType\":\"0\",\"documentNum\":\"bot_id\"}".replace(
        "bot_id", str(bot_id))
    headers = {
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {token}'.format(token=TOKEN),
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    try:
        if response.json()["msg"] == "REGISTER USER SUCCESS":
            print(response.json())
            return True
    except:
        pass
    print("add user {bot_id} failed".format(bot_id=bot_id), response.text)
    return False


with ThreadPoolExecutor(max_workers=10) as pool:
    pool.map(create_user, range(0, 99))
