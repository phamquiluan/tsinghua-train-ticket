import inspect
import random
import time
import traceback
from tempfile import NamedTemporaryFile
from typing import List, Callable, Dict

import ddddocr
from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

ocr = ddddocr.DdddOcr()


class PageOperations:
    operations = {}  # type: Dict[str, Callable]
    operation_children_dict = {}  # type: Dict[str, List[str]]

    def __init__(self):
        raise NotImplementedError()

    @staticmethod
    def run(name: str, kwargs=None):
        if kwargs is None:
            kwargs = {}
        try:
            logger.info(f"run operation {name}")
            PageOperations.operations[name](kwargs)
        except KeyError as e:
            logger.error(f"operation name {name} not found. Available operations: {', '.join(self.operations.keys())}")
            raise e

    @staticmethod
    def run_random_path(kwargs):
        path = random.choice(PageOperations.paths())
        logger.info(f"current path: {path}")
        for step in path:
            PageOperations.run(step, kwargs)

    @staticmethod
    def register(name: str, children: List[callable]):
        def wrapper(func):
            def func_wrapped(kwargs):
                parameters = inspect.signature(func).parameters
                actual_kwargs = {key: kwargs.get(key) for key in kwargs.keys() if key in parameters}
                return func(**actual_kwargs)

            PageOperations.operations[name] = func_wrapped
            PageOperations.operation_children_dict[name] = children
            return func

        return wrapper

    @staticmethod
    def paths() -> List[str]:
        return PageOperations.find_paths("begin", [])

    @staticmethod
    def find_paths(current_op, path):
        path = path + [current_op]
        paths = []
        for op in PageOperations.operation_children_dict[current_op]:
            if op not in PageOperations.operations:
                continue
            if op not in path:
                new_paths = PageOperations.find_paths(op, path)
                paths.extend(new_paths)
        if paths:
            return paths
        else:
            return [path]


@PageOperations.register("begin", ["login"])
def begin(driver, base_url):
    driver.get(f"{base_url}/index.html")
    logger.info(f"current url: {driver.current_url}")


@PageOperations.register("end", [])
def end():
    pass


@PageOperations.register("login", [
    'basic_search', 'advance_search', 'order_list1', 'consign_list1', 'order_list2', "consign_list2",
    "order_list3", "consign_list3"
])
def login(driver, username, password, base_url):
    driver.implicitly_wait(10)
    logger.info(f"login with username={username} password={password}")

    # jump to login page
    driver.get(f"{base_url}/client_login.html")
    deal_alert(driver, 2)

    login_success = False
    cnt = 0
    while cnt <= 10:
        cnt += 1
        # input username
        loginNameLabel = driver.find_element_by_id('flow_preserve_login_email')
        loginNameLabel.send_keys(' ')
        loginNameLabel.clear()
        loginNameLabel.send_keys(username)

        # input password
        loginPwdLabel = driver.find_element_by_id('flow_preserve_login_password')
        loginPwdLabel.send_keys(' ')
        loginPwdLabel.clear()
        loginPwdLabel.send_keys(password)

        with NamedTemporaryFile("wb+", suffix=".png") as file:
            driver.find_element_by_id("flow_preserve_login_verification_code_img").screenshot(file.name)
            file.seek(0)
            vc_text = ocr.classification(file.read()).upper()
            # image = Image.open(file).resize((60, 20))
            # print("ddddocr: ", ocr.classification(image.tobytes()))
            # vc_text = "".join([
            #     pytesseract.image_to_string(
            #         image.crop((6 + 13 * i, 0, 6 + 13 * (i + 1), 20)), lang="eng",
            #         config=r"--psm 10 "
            #                "-c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            #     )[0] for i in range(4)
            # ])
            logger.debug(f"try verification code {vc_text}")
        vc_label = driver.find_element_by_id('flow_preserve_login_verification_code')
        vc_label.send_keys(' ')
        vc_label.clear()
        vc_label.send_keys(vc_text)

        # click login button
        driver.find_element_by_id('client_login_button').click()
        time.sleep(2)

        if driver.find_element_by_id("flow_preserve_login_msg").text == "login success":
            login_success = True
            break
        driver.execute_script("loginApp.reloadYZM()")

    assert login_success, "login failed for too many times"
    logger.info(f"login success with username={username} password={password}")


def myWait(driver, limit=10):
    # driver.implicitly_wait(10)
    # logger.info(f"after waiting for {limit}")
    pass


def deal_alert(driver, limit=4):
    time.sleep(0.5)
    try:
        alert = WebDriverWait(driver, limit).until(expected_conditions.alert_is_present())
        logger.info(f"deal alert \"{alert.text}\"")  # 打印 alert 的信息
        driver.switch_to.alert.accept()
    except TimeoutException as e:
        pass
    except Exception as e:
        logger.info(f"something wrong when dealing alert: {e}\n{traceback.format_exc()}")
    '''
    except Exception as e:
        debugMsg(username + ' something went wrong - error: ')
        print(e.args)
        print("====")
        print(traceback.format_exc())
    '''


@PageOperations.register("order_list1", ['basic_search', 'advance_search'])
@PageOperations.register("order_list2", ['click_pay', 'click_cancel', 'click_consign'])
@PageOperations.register("order_list3", ['execute'])
def orderListPage(driver):
    deal_alert(driver, 1)
    myWait(driver, 10)
    time.sleep(0.5)
    driver.find_element_by_link_text('Order List').click()  # go to Order List page
    driver.implicitly_wait(10)
    logger.info(f"goto order list page success, current url={driver.current_url}")


@PageOperations.register("consign_list1", ['basic_search', 'advance_search'])
@PageOperations.register("consign_list2", ['order_list2'])
@PageOperations.register("consign_list3", ['execute'])
def consignListPage(driver):
    deal_alert(driver, 1)
    myWait(driver, 10)
    time.sleep(0.5)
    driver.find_element_by_link_text('Consign List').click()  # go to Consign List page
    deal_alert(driver, 2)
    logger.info(f"goto consign list page success, current url={driver.current_url}")


def adminPage(driver):
    myWait(driver, 10)
    if not str(driver.current_url).endswith('/adminlogin.html'):
        time.sleep(0.5)
        driver.find_element_by_id('goto_admin').click()  # go to Admin page
        time.sleep(1)
        logger.info(f"go to Admin, current url={driver.current_url}")

    myWait(driver, 10)
    # input username
    loginNameLabel = driver.find_element_by_id('doc-ipt-email-1')
    loginNameLabel.send_keys(' ')
    loginNameLabel.clear()
    loginNameLabel.send_keys('admin')

    # input password 并登录
    loginPwdLabel = driver.find_element_by_id('doc-ipt-pwd-1')
    loginPwdLabel.send_keys(' ')
    loginPwdLabel.clear()
    loginPwdLabel.send_keys('222222')
    driver.find_element_by_class_name('am-btn-default').click()
    time.sleep(1)


@PageOperations.register("execute", ['end'])
def execute(driver):
    flows = ['Enter Station', 'Ticket Collect']
    driver.implicitly_wait(10)
    # try :
    # jump to ticket reserve page
    # driver.find_element_by_link_text('Ticket Reserve').click()
    time.sleep(1)

    driver.find_element_by_link_text('Execute Flow').click()
    WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, 'Ticket Collect')),
                                   message='Timeout!!').click()
    WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, 'reserve_collect_button')),
                                   message='Timeout!!').click()
    deal_alert(driver, 5)
    deal_alert(driver, 5)
    WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, 'Enter Station')),
                                   message='Timeout!!').click()
    time.sleep(0.5)
    WebDriverWait(driver, 5).until(
        expected_conditions.element_to_be_clickable((By.ID, 'enter_reserve_execute_order_button')),
        message='Timeout!!').click()
    deal_alert(driver, 5)
    deal_alert(driver, 5)
    time.sleep(0.5)
    logger.info("Ticket collection and station entering success")


@PageOperations.register("logout", ["login"])
def logout(driver):
    myWait(driver, 10)
    time.sleep(0.5)
    driver.find_element_by_id('logout_button').click()
    deal_alert(driver, )
    logger.info(f"logout success, current url={driver.current_url}")


def select_contacts(driver):
    driver.implicitly_wait(10)
    time.sleep(1)
    deal_alert(driver, 1)
    WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.NAME, 'booking_contacts'))).click()
    # select assurance, food and so on
    Select(driver.find_element_by_id('assurance_type')).select_by_value('1')
    driver.find_element_by_id('need-food-or-not').click()
    time.sleep(1)
    Select(driver.find_element_by_id('preserve_food_type')).select_by_value('1')
    time.sleep(1)
    try:
        Select(driver.find_element_by_id('train-food-type-list')).select_by_value('1')
    except Exception as e:
        logger.warning(f"{e}")
    time.sleep(1)
    driver.find_element_by_id('ticket_select_contacts_confirm_btn').click()
    logger.info(f"select contacts success, current url={driver.current_url}")


# submit booking
def confirm_booking(driver):
    myWait(driver, 10)
    confirm = driver.find_element_by_id('my-prompt').find_elements_by_class_name('am-modal-btn')[1]
    time.sleep(0.5)
    confirm.click()
    deal_alert(driver, )
    try:
        WebDriverWait(driver, 10).until(expected_conditions.alert_is_present()).accept()
    except Exception as e:
        logger.warning(f"Exception: {e}")
    time.sleep(0.5)
    logger.info(f"confirm book success, current url={driver.current_url}")


def isClassExist(driver, class_name):
    flag = False
    try:
        driver.find_element_by_class_name(class_name)
        flag = True
    except NoSuchElementException:
        pass
    finally:
        return flag


ROUTES = [
    ["Nan Jing", "Zhen Jiang", "Wu Xi", "Su Zhou", "Shang Hai"],
    ["Shang Hai", "Su Zhou"],
    ["Shang Hai", "Nan Jing", "Tai Yuan"],
    ["Nan Jing", "Xu Zhou", "Ji Nan", "Bei Jing"],
    ["Tai Yuan", "Nan Jing", "Shang Hai"]
]


def fill_station_name(driver):
    route = random.choice(ROUTES)
    start_id = random.randint(0, len(route) - 1)
    end_id = random.randint(0, len(route) - 1)
    while end_id == start_id:
        end_id = random.randint(0, len(route) - 1)
    if start_id > end_id:
        start_id, end_id = end_id, start_id
    start_name = route[start_id]
    term_name = route[end_id]
    start = driver.find_element_by_id('travel_booking_startingPlace')
    start.clear()
    start.send_keys(start_name)
    term = driver.find_element_by_id('travel_booking_terminalPlace')
    term.clear()
    term.send_keys(term_name)
    try:
        Select(driver.find_element_by_id('search_select_train_type')).select_by_index(0)
    except:
        pass  # Advanced search


@PageOperations.register("basic_search", ["order_list2", "end"])
def booking_ticket_via_basic_search(driver):
    driver.implicitly_wait(10)
    # jump to ticket reserve page
    driver.find_element_by_link_text('Ticket Reserve').click()

    fill_station_name(driver)

    # click search button
    driver.find_element_by_id('travel_searching_button').click()

    WebDriverWait(driver, 60).until(
        expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'ticket_booking_button')), message='Timeout!!')

    trip_table_item = random.choice(
        driver.find_element_by_id("tickets_booking_list_table").find_element_by_css_selector("tbody")
            .find_elements_by_css_selector("tr")
    )  # type: WebElement
    logger.info(f"select trip item {trip_table_item.text}")

    booking_button = trip_table_item.find_element_by_class_name('ticket_booking_button')

    # select seat
    seat_select = trip_table_item.find_elements_by_class_name('booking_seat_class')[0]  # type: WebElement
    seat_options = seat_select.find_elements_by_css_selector('*')
    seat_choice = random.choice(seat_options)
    seat_choice.click()
    logger.info(f"select seat {seat_choice.text}")

    booking_button.click()

    # select assurance, food and so on
    select_contacts(driver, )

    confirm_booking(driver, )

    driver.refresh()
    time.sleep(0.5)


@PageOperations.register("advanced_search", ["order_list2", "end"])
def bookingTicketViaAdvancedSearch(driver):
    myWait(driver, 10)
    # jump to advanced search page
    driver.find_element_by_link_text('Advanced Search').click()
    time.sleep(0.5)

    fill_station_name(driver)

    # click search button
    driver.find_element_by_id('ad_search_booking_button').click()
    WebDriverWait(driver, 60).until(
        expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'ticket_booking_button')),
        message='Timeout!!')
    bookingButton = random.choice(driver.find_elements_by_class_name('ticket_booking_button')).click()

    # select assurance, food and so on
    select_contacts(driver, )

    confirm_booking(driver, )

    driver.refresh()
    time.sleep(0.5)


@PageOperations.register("click_pay", ["order_list3", "consign_list3", "end"])
def pay(driver):
    # click pay button
    btns = driver.find_elements_by_class_name('am-btn')  # type: List[WebElement]
    btns = [btn for btn in btns if btn.text == 'Pay']
    if len(btns) > 0:
        random.choice(btns).click()
    else:
        logger.warning("No payment button to click")
        return

    WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable((By.ID, 'pay_for_preserve')),
                                    message='Timeout!!').click()
    deal_alert(driver, 5)
    logger.info("payment success")


@PageOperations.register("click_cancel", ["end"])
def cancel(driver):
    # click cancel button
    btns = driver.find_elements_by_class_name('am-btn')
    btns = [btn for btn in btns if btn.text == 'Cancel']
    if len(btns) > 0:
        random.choice(btns).click()
    else:
        logger.warning("No cancel button to click")
        return
    WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, 'ticket_cancel_panel_confirm')),
                                   message='Timeout!!').click()
    # driver.find_element_by_id('ticket_cancel_panel_confirm').click()
    # WebDriverWait(driver, 20).until(EC.alert_is_present()).accept()
    deal_alert(driver, )
    time.sleep(0.5)


@PageOperations.register("click_consign", ["end"])
def click_consign(driver):
    btns = driver.find_elements_by_class_name('am-btn')
    btns = [btn for btn in btns if btn.text == 'Consign']
    if len(btns) > 0:
        random.choice(btns).click()
    else:
        logger.warning("No consign button to click")
        return
    WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, 'submit_for_consign')))
    driver.find_element_by_id('re_booking_name').send_keys("consign name {}".format(random.randint(0, 99)))
    phone_number = ''.join([str(random.randint(0, 9)) for i in range(11)])
    driver.find_element_by_id('re_booking_phone').send_keys(phone_number)
    driver.find_element_by_id('re_booking_weight ').send_keys(str(random.randint(1, 50)))
    driver.find_element_by_id('submit_for_consign').click()
    deal_alert(driver, )
    time.sleep(0.5)


def adminDelOrder(driver):
    try:
        driver.refresh()
        driver.implicitly_wait(1)
        # 查看是否有可以删除的订单
        delBtns = driver.find_elements_by_class_name('am-text-danger')
        if len(delBtns) == 0:
            return False
        # 随机删除其中一个订单
        delBtn = random.choice(delBtns)
        delBtn.click()
        # 确认删除操作
        confirm = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'delete_confirm')))
        time.sleep(0.5)
        confirm.find_elements_by_class_name('am-modal-btn')[1].click()
        deal_alert(driver, )
        time.sleep(0.5)
        return True
    except:
        return True


def adminDirectPage(driver, page):
    # 进入一个在主页上可以直接点击进入的页面（admin mode）
    myWait(driver, 10)
    driver.find_element_by_link_text(page).click()
    time.sleep(1)


def adminIndirectPage(driver, page):
    # 进入一个在主页上不可以直接点击进入的页面， 需要先点击“Basic”（admin mode）
    myWait(driver, 10)
    driver.find_element_by_link_text('Basic').click()
    time.sleep(0.1)
    WebDriverWait(driver, 2).until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, page)),
                                   message='Timeout!!').click()
    time.sleep(1)
    driver.find_element_by_link_text('Basic').click()


__all__ = ["PageOperations"]
#
#
# def defineGraph():
#     graph = {
#         'begin': ['logout'],
#         'logout': ['login'],
#         'login': ['basic_search', 'advance_search', 'order_list1', 'consign_list1'],
#         'order_list1': ['basic_search', 'advance_search'],
#         'consign_list1': ['basic_search', 'advance_search'],
#         'order_list2': ['click_pay', 'click_cancel', 'click_consign'],
#         'consign_list2': ['order_list2'],
#         'order_list3': ['execute'],
#         'consign_list3': ['execute'],
#         'basic_search': ['booking'],
#         'advance_search': ['booking'],
#         'booking': ['contact'],
#         'contact': ['personalize'],
#         'personalize': ['click_select'],
#         'click_select': ['click_submit'],
#         'click_submit': ['order_list2', 'consign_list2'],
#         'click_pay': ['order_list3', 'consign_list3'],
#         'click_cancel': ['finish'],
#         'click_consign': ['input_consign_info'],
#         'input_consign_info': ['click_pay'],
#         'execute': ['finish']
#
#     }
#     return graph
#
#
# def defineOperation():
#     operations = {
#         'logout': logout,
#         'login': login,
#         'order_list1': orderListPage,
#         'consign_list1': consignListPage,
#         'order_list2': orderListPage,
#         'consign_list2': consignListPage,
#         'order_list3': orderListPage,
#         'consign_list3': consignListPage,
#         'basic_search': bookingTicketViaBasicSearch,
#         'advance_search': bookingTicketViaAdvancedSearch,
#         'click_pay': pay,
#         'click_cancel': cancel,
#         # 'click_consign': ['input_consign_info'],
#         # 'input_consign_info': ['order_list3', 'consign_list3'],
#         'execute': execute
#
#     }
#     return operations
