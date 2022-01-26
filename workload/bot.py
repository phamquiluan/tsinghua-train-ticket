import gc
import sys
import time
import math
import random
import threading
import argparse
import traceback
from concurrent.futures.process import ProcessPoolExecutor

import loguru
from loguru import logger

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains  # 导入模块
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from multiprocessing import Process
from page_operations import PageOperations

DEBUG_FLAG = True

BUBBLE_TIME = 0
EXEC_CNT = 0
PERIOD = 24 * 60 * 60
PEAK_LIST = [
    (0.2, 43200, 30000),
    (0.4, 39600, 5400),
    (0.8, 68400, 7200)
]

def calc_prob(t):
    ret = 0
    t = (t * 24) % PERIOD  # 放缩到每小时为一个周期
    for coef, center, sigma in PEAK_LIST:
        if t <= center:
            dist = min(center - t, t + PERIOD - center)
        else:
            dist = min(t - center, center + PERIOD - t)
        ret += coef * math.exp(-dist * dist / (2 * sigma * sigma))
    return ret

def current_prob():
    cur = time.localtime(time.time() + time.timezone + 28800)
    # always use UTF+8
    cur_sec = (cur.tm_hour * 60 + cur.tm_min) * 60 + cur.tm_sec
    return calc_prob(cur_sec)

def emulate_user_behaviour(username, password, threads, main_page, binary_path="google-chrome"):
    option = webdriver.ChromeOptions()
    option.binary_location = binary_path
    option.add_argument(
        "--user-agent=\
        Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    )
    option.add_argument('--headless')  # 取消浏览器的可视化展示
    option.add_argument('--no-sandbox')  # 禁用沙盒模式
    option.add_argument('--disable-dev-shm-usage')
    option.add_argument('blink-settings=imagesEnabled=true')
    option.add_argument('--disable-gpu')
    option.add_argument("service_args = ['–ignore - ssl - errors = true', '–ssl - protocol = TLSv1', '--verbose']")
    option.add_argument('window-size=1440x900')  # 设置浏览器窗口大小
    #    option.add_argument('port={}'.format(30007 + int(username[5 : ])))
    #    option.add_argument('--start-maximized')
    logger.debug(f"all paths: {PageOperations.paths()}")

    def execute():
        driver = webdriver.Chrome(options=option)
        kwargs = {
            "username": username, "password": password, "base_url": main_page, "driver": driver
        }
        try:
            PageOperations.run_random_path(kwargs)
        except Exception as e:
            print('{} failed because {}, into next itr'.format(username, e))
            print(e.args)
            print("====")
            print(traceback.format_exc())
        driver.quit()

    global BUBBLE_TIME, EXEC_CNT
    while True:
        p = current_prob()
        logger.info(f"current executing probability is {p}")
        if random.random() <= p:
            start = time.time()
            execute()
            cur = time.time() - start
            BUBBLE_TIME += (cur - BUBBLE_TIME) / (EXEC_CNT + 1)
            EXEC_CNT += 1
            logger.info(f"bubble time updated to {BUBBLE_TIME}")
        else:
            logger.info("sleep in this turn")
            time.sleep(BUBBLE_TIME)


def main():
    parser = argparse.ArgumentParser(description='Ticket bot')
    parser.add_argument('--threads', type=int, default=1)
    parser.add_argument('--username', default="fdse_microservice")
    parser.add_argument('--password', default="111111")
    parser.add_argument('--executable-path', default="google-chrome")
    parser.add_argument('--main-page', default="http://train-ticket1.cluster.peidan.me:32677")
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()

    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
               f"| <yellow>[username={args.username}]</yellow>"
               "| <level>{level: <8}</level> "
               "| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level="DEBUG" if args.debug else "INFO"
    )

    logger.debug(f"args={args}")
    emulate_user_behaviour(args.username, args.password, args.threads, args.main_page, args.executable_path)


if __name__ == '__main__':
    main()
