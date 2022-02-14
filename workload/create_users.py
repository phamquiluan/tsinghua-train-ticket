import os
from concurrent.futures import ThreadPoolExecutor

import requests

URL = os.environ.get('TRAIN_TICKET_URL', 'http://localhost:32677')


def get_admin_token():
    url = "{URL}/api/v1/users/login".format(URL=URL)
    payload = "{\n    \"username\": \"admin\",\n    \"password\": \"222222\"\n}"
    headers = {
        'Content-Type': 'application/json;charset=utf-8',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Host': 'lzy-k8s-1.cluster.peidan.me:32677',
        'Origin': 'http://lzy-k8s-1.cluster.peidan.me:32677',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15',
        'Connection': 'keep-alive',
        'Referer': 'http://lzy-k8s-1.cluster.peidan.me:32677/adminlogin.html',
        'Content-Length': '40',
        'Cookie': 'YsbCaptcha=D5F232C369CF4658859F57ADA50EF003; JSESSIONID=B5CD7ED28460FE80533BD61A574B18F9; redirect_to=%2Ffavicon.ico; grafana_session=22fdcb946af0629c232e8238dc49fac7',
        'Proxy-Connection': 'keep-alive'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    try:
        return response.json()['data']['token']
    except Exception as e:
        print(response.text)
        raise e


TOKEN = get_admin_token()


def create_user(bot_id):
    print(bot_id)
    url = "{URL}/api/v1/adminuserservice/users".format(URL=URL)
    payload = "{\"userName\":\"bots-bot_id\",\"password\":\"bot\",\"gender\":\"0\",\"email\":\"bots-bot_id@train-ticket1.peidan.me\",\"documentType\":\"0\",\"documentNum\":\"bot_id\"}".replace(
        "bot_id", str(bot_id))
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer   {token}'.format(token=TOKEN),
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36 Edg/85.0.564.68',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'http://train-ticket1:32677',
        'Referer': 'http://train-ticket1:32677/admin_user.html',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cookie': 'JSESSIONID=AB07591BBBACD73784DD91730196B9FA; grafana_session=42deacba680f9c00f2385af30e8e38cf'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text.encode('utf8'))


with ThreadPoolExecutor(max_workers=10) as pool:
    pool.map(create_user, range(0, 100))
