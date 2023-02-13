import argparse
import math
import random
import sys
import time
import traceback

from loguru import logger
from selenium import webdriver

from page_operations import PageOperations

DEBUG_FLAG = True

BUBBLE_TIME = 0
EXEC_CNT = 0
PERIOD = 24 * 60 * 60
PEAK_LIST = [
    (1, 43200, 36000),
    (0.2, 36000, 7200),
    (0.2, 57600, 7200)
]


def calc_prob(t):
    ret = 0
    t = (t * 17) % PERIOD
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
    option.add_argument('--headless')  # cancel browser's visual display
    option.add_argument('--no-sandbox')  # disable sandbox mode
    option.add_argument('--disable-dev-shm-usage')
    option.add_argument('blink-settings=imagesEnabled=true')
    option.add_argument('--disable-gpu')
    option.add_argument("service_args = ['–ignore - ssl - errors = true', '–ssl - protocol = TLSv1', '--verbose']")
    option.add_argument('window-size=1440x900')  # 
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
