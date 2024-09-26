import requests
import time
import re
import sys, os
import json
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import shutil
import eel
import socket
from bs4 import BeautifulSoup
import tempfile
import threading
import random
import sounddevice as sd
import soundfile as sf
from random import choice
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import urllib3


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = '15aFBq6GSuaF8L6dFsA4Aw141dQy2s6N_MKZHgvpdSjo'

R_TABLE = {}

urllib3.disable_warnings()

class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = os.path.normpath(tempfile.mkdtemp())

        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        shutil.rmtree(self._dir)


def selenium_connect(proxy=None, adspower_api=None, adspower_number=None):
    print(proxy)
    driver = ''
    if adspower_api and adspower_number:
        options = Options()
        options.add_argument("--start-maximized")
        #options.add_argument("--incognito")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--lang=EN')
        cwd= os.getcwd()
        slash = "\\" if sys.platform == "win32" else "/"
        directory_name = cwd + slash + "uBlock-Origin"
        directory_name2 = cwd + slash + "vpn"
        extension = os.path.join(cwd, directory_name)
        extension2 = os.path.join(cwd, directory_name2)
        print(extension, extension2)
        # if proxy and proxy != 'vpn':
        #     proxy = proxy.split(":", 3)
        #     proxy[1] = int(proxy[1])
        #     print(proxy)
        #     proxy_extension = ProxyExtension(*proxy)
        #     options.add_argument(f"--load-extension={proxy_extension.directory},{extension}")
        
        from selenium import webdriver
        print(' IN ADSPOWER CONNECTION ')
        open_url = adspower_api + "/api/v1/browser/start?serial_number=" + adspower_number

        resp = requests.get(open_url).json()
        if resp["code"] != 0:
            print(resp["msg"])
            print("please check ads_id")
            sys.exit()

        chrome_driver = resp["data"]["webdriver"]
        service = Service(executable_path=chrome_driver)
        chrome_options = Options()



        chrome_options.add_experimental_option("debuggerAddress", resp["data"]["ws"]["selenium"])
        driver = webdriver.Chrome(service=service, options=chrome_options)

    elif not adspower_api and not adspower_number:
        import undetected_chromedriver as webdriver
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        #options.add_argument("--incognito")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--lang=EN')
        cwd= os.getcwd()
        slash = "\\" if sys.platform == "win32" else "/"
        directory_name = cwd + slash + "uBlock-Origin"
        directory_name2 = cwd + slash + "vpn"
        extension = os.path.join(cwd, directory_name)
        extension2 = os.path.join(cwd, directory_name2)
        print(extension, extension2)
        if proxy and proxy != 'vpn':
            proxy = proxy.split(":", 3)
            proxy[1] = int(proxy[1])
            print(proxy)
            proxy_extension = ProxyExtension(*proxy)
            options.add_argument(f"--load-extension={proxy_extension.directory},{extension}")
        prefs = {"credentials_enable_service": False,
            "profile.password_manager_enabled": False}
        options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(
            options=options,
            enable_cdp_events=True,
        )

    # screen_width, screen_height = driver.execute_script(
    #     "return [window.screen.width, window.screen.height];")
    
    # desired_width = int(screen_width / 2)
    # desired_height = int(screen_height / 3)
    # driver.set_window_position(0, 0)
    # driver.set_window_size(screen_width, screen_height)
    # set_random_16_9_resolution(driver)

    return driver


def set_random_16_9_resolution(driver):
    # Define the range of resolutions
    min_width, max_width = 1366, 1920
    min_height, max_height = 768, 1080

    # Generate random width and height within the specified range
    width = random.randint(min_width, max_width)
    height = random.randint(min_height, max_height)

    # Set the window size
    driver.set_window_size(width, height)


def get_data_from_google_sheets():
    try:
        # Authenticate with Google Sheets API using the credentials file
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        # Connect to Google Sheets API
        service = build("sheets", "v4", credentials=creds)

        # Define the range to fetch (assuming the data is in the first worksheet and starts from cell A2)
        range_name = "main!A2:Q"

        # Fetch the data using batchGet
        request = service.spreadsheets().values().batchGet(spreadsheetId=SPREADSHEET_ID, ranges=[range_name])
        response = request.execute()

        # Extract the values from the response
        values = response['valueRanges'][0]['values']

        return values

    except HttpError as error:
        print(f"An HTTP error occurred: {error}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def extract_price(raw_price):
  # Use regex to find all digit sequences with optional decimal points
  match = re.search(r'(\d+[.,]?\d*)', raw_price)
  
  if match:
      # Replace any comma with a dot for proper float conversion
      price_str = match.group(1).replace(',', '.')
      price = float(price_str)
      return int(price) if price.is_integer() else price
  return None  # Return None if no valid price found


def wait_for_button(driver):
    try:
        if WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="reserveError"]'))):
            driver.find_element(By.CSS_SELECTOR, 'div[data-testid="reserveView"] > div > button > span').click()
            return True
    except:
        return False

def look_for_tickets(driver):
    try:
        element = check_for_element(driver, "section[data-testid='panel']")
        if element:
            check_for_element(driver, 'span[class="indexstyles__CustomCheckbox-sc-ruvmzp-6 kOIrjE"]', click=True)
            check_for_element(driver, 'button[class="indexstyles__StyledButton-sc-83qv1q-0 PXcYf sc-dzmfew-6 bAoxae"]', click=True)
        return True
    except: return False



def wait_for_something(driver, selector):
    try:
        if WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))):
            return True
    except: return False


def wait_for_clickable(driver, selector):
    try:
        if WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))):
            return True
    except: return False


def wait_for_element(driver, selector, click=False, timeout=10, xpath=False, debug=False, scrollToBottom=False):
    try:
        if xpath:
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, selector)))
        else:
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        
        if click:
            driver.execute_script("arguments[0].scrollIntoView();", element)
            if scrollToBottom: driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", check_for_element(driver, '#main-content'))
            element.click()
        return element
    except Exception as e:
        if debug: print("selector: ", selector, "\n", e)
        return False


def check_for_element(driver, selector, click=False, xpath=False, debug=False):
    try:
        if xpath:
            element = driver.find_element(By.XPATH, selector)
        else:
            element = driver.find_element(By.CSS_SELECTOR, selector)
        if click: 
            driver.execute_script("arguments[0].scrollIntoView();", element)
            # slow_mouse_move_to_element(driver, element)
            element.click()
        return element
    except Exception as e: 
        if debug: print("selector: ", selector, "\n", e)
        return False

def check_for_elements(driver, selector, xpath=False, debug=False):
    try:
        if xpath:
            element = driver.find_elements(By.XPATH, selector)
        else:
            element = driver.find_elements(By.CSS_SELECTOR, selector)
        return element
    except Exception as e: 
        if debug: print("selector: ", selector, "\n", e)
        return False


def slow_mouse_move_to_element(driver, element):
    action_chains = ActionChains(driver)
    action_chains.move_to_element(element)
    action_chains.perform()
    # Get current mouse position
    current_x = driver.execute_script("return window.scrollX")
    current_y = driver.execute_script("return window.scrollY")
    start_x = current_x
    start_y = current_y
    # Get target element position
    target_x = element.location['x']
    target_y = element.location['y']
    # Calculate distance to move
    distance_x = target_x - current_x
    distance_y = target_y - current_y
    # Number of steps
    steps = 10
    # Perform small movements with delays
    for step in range(steps):
        current_x += distance_x / steps
        current_y += distance_y / steps
        driver.execute_script("window.scrollTo({}, {})".format(int(current_x), int(current_y)))
        time.sleep(random.uniform(0.1, 0.3))  # Add random delay


def write_error_to_file(error_message):
    with open('error_log.txt', 'a') as file:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        file.write(f'{timestamp}: {error_message}\n')


def send_cookies(driver):
    cookies = driver.get_cookies()
    cookies_json = json.dumps(cookies)
    return cookies_json


def post_request(data, endpoint='/book'):
    try:
        json_data = json.dumps(data)
        
    except Exception as e:
        print(e)
    # Set the headers to specify the content type as JSON
    headers = {
        "Content-Type": "application/json"
    }

    # Send the POST request
    try:
        response = requests.post(f"http://localhost:808{endpoint}", data=json_data, headers=headers)
        print(response)
    except Exception as e:
        print(e)
    # Check the response status code
    if response.status_code == 200:
        print("POST request successful!")
    else:
        print("POST request failed.")


def change_ip(url):
    try:
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
           return True
        else:
            print(f"Request failed with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def reconnect_vpn(driver, link):
    blacklist = ['Iran', 'Egypt', 'Italy']
    while True:
        try:
            driver.get('chrome-extension://koaohlpdpbbicmhnhmccmkmbppgpocnj/popup/index.html')
            wait_for_element(driver, 'button[class="button button--pink consent-text-controls__action"]', click=True, timeout=5)
            is_connected = check_for_element(driver, 'div[class="play-button play-button--pause"]')
            if is_connected: 
                driver.find_element(By.CSS_SELECTOR, 'div[class="play-button play-button--pause"]').click()
            print('select-location')
            select_element = driver.find_element(By.CSS_SELECTOR, 'div[class="select-location"]')
            print('click-select')
            select_element.click()
            print('random-choice')
            time.sleep(2)
            while True:
                element = random.choice(check_for_elements(driver, '//ul[@class="locations"][2]/li/p', xpath=True))
                element_text = element.text
                print(element_text)
                if element_text not in blacklist: break
            driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
            time.sleep(5)
            driver.get(link)
            break
        except Exception as e: pass


def create_new_connection(proxy, link):
    while True:
        try:
            driver = selenium_connect(proxy)
            driver.get(link)
            return driver
        except:
            driver.close()
            driver.quit()


def get_random_line():
    file_path = os.path.join(os.getcwd(), 'uas.txt')
    print(file_path)
    with open(file_path, 'r') as file:
        lines = file.readlines()
        random_line = random.choice(lines)
    return random_line.strip()


def queue_bypass(driver, email, password):
    print('in queue bypass')
    if not check_for_element(driver, 'a[href="sign-out"]'):
        while True:
            driver.refresh()
            wait_for_element(driver, 'button[data-event-label="Lobby Join the Queue Button"]', click=True)
            email_input = wait_for_element(driver, 'input[name="email"]', debug=True, click=True, timeout=30)
            if email_input: break
    else: wait_for_element(driver, 'button[data-event-label="Lobby Join the Queue Button"]', click=True)
    email_input.send_keys(email)
    password_input = check_for_element(driver, 'input[name="password"]', click=True)
    password_input.send_keys(password)
    check_for_element(driver, 'button[type="submit"]', True)
    wait_for_element(driver, 'button[data-bdd="next-button"]', timeout=10, click=True)
    print(f'Managed to enter email: {email}')
    while True:
        wait_for_element(driver, 'button[data-event-label="Lobby Join the Queue Button"]', click=True, timeout=5)
        already_in_line = wait_for_element(driver, 'h3[data-bdd="error-already-in-line-heading"]', timeout=5)
        wait_for_element(driver, 'button[data-event-category="Queue Error"]', timeout=5, click=True)
        is_queue = wait_for_element(driver, 'body > iframe.child_frame', timeout=5)
        if already_in_line:
            check_for_element(driver, 'button[data-bdd="error-already-in-line-cta-button"]', click=True)
            print('Clicked on already in line button')
        elif is_queue: break
    queue_iframe = wait_for_element(driver, 'body > iframe.child_frame', timeout=5)
    driver.switch_to.frame(queue_iframe)
    while True:
        queue_counter = check_for_element(driver, 'h2[data-bdd="statusСard-peopleInLine-count"]')
        print(queue_counter.text)
        try:
            if (int(queue_counter.text)): break
        except: 
            time.sleep(5)
            continue
    while True:
        queue_counter = check_for_element(driver, 'h2[data-bdd="statusСard-peopleInLine-count"]')
        if int(queue_counter.text) < 100000:
            pass
        if not queue_counter or check_for_element(driver, '#buttonConfirmRedirect', click=True):
            break
    return True


def process_type_1(driver):
  global data
  link = data['link']
  category_amount_dict = data['category_amount_dict']
  proxy = data['proxy']
  price = data['price']
  reload_time = int(data['refresh_interval'])
  ranged_price = parse_range(price[0])
  invitation_code = data['invitation_code']
  print('INVITATION CODE')
  print('INVITATION CODE', invitation_code)
  print('CATEGORIES', category_amount_dict)
  # driver = ''
  # print("ADSPOWER", adspower)
  # if not adspower:
  #   temp_proxy = 'vpn'
  #   if proxy != 'vpn':
  #       temp_proxy = proxy if not isinstance(proxy, list) else choice(proxy)
  #   driver = create_new_connection(temp_proxy, link)
  #   time.sleep(2)
  #   if proxy == 'vpn':
  #       tabs = driver.window_handles
  #       driver.switch_to.window(tabs[1])
  #       driver.close()
  #       driver.switch_to.window(tabs[0])
  #   if proxy == 'vpn': reconnect_vpn(driver, link)
  # elif adspower:
  #     if not proxy:
  #       print('NOT PROXY')
  #       driver = selenium_connect('', adspower)
  #     elif proxy != 'vpn':
  #       print('PROXY != vpn')
  #       temp_proxy = proxy if not isinstance(proxy, list) else choice(proxy)
  #     elif proxy:
  #       print('PROXY')
  #       pass
  while True:
    print('in while True')
    try:
        driver.refresh()
        # try:
        #     is_queue = wait_for_element(driver, '//*[contains(text(), "Join the Queue")]', xpath=True, click=True)
        #     if is_queue: input('continue?')
        # except: pass
        try:
            driver.find_element(By.CSS_SELECTOR, 'div[id="t1"]')
            print('block')
            if proxy == "vpn":
                if reload_time: time.sleep(reload_time)
                # driver.delete_all_cookies()
                set_random_16_9_resolution(driver)
                reconnect_vpn(driver, link)
            if reload_time: time.sleep(reload_time)
            else: time.sleep(60)
            continue
        except: pass
        try:
            check_for_element(driver, '#onetrust-reject-all-handler', click=True)
            driver.find_element(By.XPATH, '//div[text()="Pardon the Interruption"]')
            if reload_time: time.sleep(reload_time)
            else: time.sleep(45)
            driver.refresh()
        except: pass
        input_invitation = wait_for_element(driver,'input[placeholder="Enter Code"]', timeout=2, click=True, debug=True)
        if input_invitation:
          input_invitation.send_keys(invitation_code)
          wait_for_element(driver, '//section/form/button[@type="submit"]', timeout=2, xpath=True, click=True, debug=True)
        check_for_element(driver, '#onetrust-reject-all-handler', click=True)
        tickets_tab = check_for_element(driver, '//aside[@aria-label="Seat Map"]/div[1]/button[2]', xpath=True, click=True)
        if not tickets_tab: print("did not manage to click on 'Find seats for me'")
        # try:
        #     driver.find_element(By.CSS_SELECTOR, 'svg[class="BaseSvg-sc-yh8lnd-0 MagnifyingGlassIcon___StyledBaseSvg-sc-1pooy9n-0 ckLyyv"]').click()
        # except: pass
        ticket_data = {}
        wait_for_element(driver, '//*[@id="list-view"]/div/div[1]/ul/li', timeout=5, xpath=True)
        tickets = check_for_elements(driver, '//*[@id="list-view"]/div/div[1]/ul/li', xpath=True)
        if not tickets: 
            print('no tickets')
            if reload_time: time.sleep(reload_time)
            else: time.sleep(45)
            continue
        #//span[contains(text(), 'Unlock')]
        for ticket in tickets:
            if invitation_code:
              print('invitation', ticket)
              if check_for_element(driver, "//span[contains(text(), 'Unlock')]", xpath=True, click=True):
                  input_invitation = wait_for_element(driver,'input[placeholder="Enter Code"]', timeout=2, click=True)
                  input_invitation.send_keys(invitation_code)
                  wait_for_element(driver, '//section/form/button[@type="submit"]', timeout=2, xpath=True, click=True)
        
        wait_for_element(driver, '//*[@id="list-view"]/div/div[1]/ul/li', timeout=5, xpath=True)
        tickets = check_for_elements(driver, '//*[@id="list-view"]/div/div[1]/ul/li', xpath=True)
        
        if not tickets: 
            print('no tickets')
            if reload_time: time.sleep(reload_time)
            else: time.sleep(45)
            continue
        for ticket in tickets:
            category_raw = check_for_element(ticket, './/div[1]/div[1]/div/span[1]', xpath=True)
            category = category_raw.text.split('\n')[0]
            ticket_price_raw = check_for_element(ticket, './/div[1]/div/div/span[2]', xpath=True)
            ticket_price = extract_price(ticket_price_raw.text)
            
            # price = extract_price(ticket.find_element(By.CSS_SELECTOR, 'span[class="sc-148tjjv-5 chohwl"]').text)
            ticket_data[category] = {"ticket": ticket, "price":ticket_price}
        limit = True
        
        while limit:
            if ticket_data:
                check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                # Randomly choose a key from ticket_data
                while True:
                    random_key = choice(list(ticket_data.keys()))
                    random_key_value = ticket_data[random_key]
                    random_price = random_key_value['price']
                    if len(category_amount_dict) == 0: break
                    if len(category_amount_dict) == 1 and list(category_amount_dict.keys())[0] == '': break
                    if random_price <= int(ranged_price[0]) or random_price >= int(ranged_price[1]): continue
                    if random_key not in category_amount_dict.keys(): continue
                    break

                selected_entry = ticket_data[random_key]
                ticket = selected_entry['ticket']
                plus = ticket.find_element(By.CSS_SELECTOR, 'button[data-testid="tselectionSpinbuttonPlus"]')

                if len(category_amount_dict) == 0:
                    print('IN ELSE')
                    slow_mouse_move_to_element(driver, plus)
                    while True:
                        try: 
                            plus.click()
                            if check_for_element(ticket, 'button[data-testid="tselectionSpinbuttonPlus"][disabled]') or check_for_element(driver, 'p[data-testid="ticketLimitMsg"]'): break
                        except: pass

                elif category_amount_dict[random_key]:
                    print('IN ELIF')
                    amount_range = parse_range(category_amount_dict[random_key])
                    necessary_amount = ''
                    if amount_range:
                        necessary_amount = random.randint(amount_range[0], amount_range[1])
                    else: necessary_amount = category_amount_dict
                    print(necessary_amount)
                    amount = int(ticket.find_element(By.CSS_SELECTOR, 'span[data-testid="tselectionSpinbuttonValue"]').text)
                    slow_mouse_move_to_element(driver, plus)
                    for i in range (int(necessary_amount) - amount):
                        try: 
                            plus.click()
                            if driver.find_element(By.CSS_SELECTOR, 'p[data-testid="ticketLimitMsg"]'): break
                        except: pass
                
                elif len(category_amount_dict) == 1 and safe_list_get(list(category_amount_dict.keys()), 0) == '':
                    print(' IN IF')
                    if category_amount_dict['']:
                        amount_range = parse_range(category_amount_dict[''])
                        necessary_amount = ''
                        if amount_range:
                            necessary_amount = random.randint(amount_range[0], amount_range[1])
                        else: necessary_amount = category_amount_dict
                        print(necessary_amount)
                        amount = int(ticket.find_element(By.CSS_SELECTOR, 'span[data-testid="tselectionSpinbuttonValue"]').text)
                        slow_mouse_move_to_element(driver, plus)
                        for i in range (int(necessary_amount) - amount):
                            try: 
                                
                                plus.click()
                                if driver.find_element(By.CSS_SELECTOR, 'p[data-testid="ticketLimitMsg"]'): break
                            except: pass
                    else:
                        slow_mouse_move_to_element(driver, plus)
                        while True:
                            try: 
                                plus.click()
                                if driver.find_element(By.CSS_SELECTOR, 'p[data-testid="ticketLimitMsg"]'): break
                            except: pass
                print('nothing')
                # Trying to buy ticket with choosen settings
                for _ in range(0, 10):
                  print('in loop')
                  check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                  check_for_element(driver, 'button[data-testid="findTicketsBtn"]', click=True)
                  check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                  wait_for_element(driver, '//*[contains(text(), "I have read and agree to the above terms")]', xpath=True, timeout=2, click=True)
                  check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                  wait_for_element(driver, "//*[contains(text(), 'Proceed to Buy')]", click=True, xpath=True, timeout=2)
                  check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                  check_for_element(driver, '//span/*[contains(text(), "Accept and continue")]', xpath=True, click=True)
                  check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                  wait_for_button(driver)
                  wait_for_element(driver, '//*[contains(text(), "I have read and agree to the above terms")]', xpath=True, timeout=2)
                  check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                  if check_for_element(driver, '//div[@data-testid="reserveError"]/*[contains(text(), "Something went wrong...")]', xpath=True)\
                  or check_for_element(driver, '//div[@data-testid="reserveError"]/*[contains(text(), "Ticket Purchase Blocked")]', xpath=True):
                    if reload_time: time.sleep(int(reload_time))
                    # driver.delete_all_cookies()
                    set_random_16_9_resolution(driver)
                    if proxy == "vpn":
                      reconnect_vpn(driver, link)
                      break
                    break
                  check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                  if look_for_tickets(driver): 
                    if 'checkout' in driver.current_url:
                      data_to_play, fs = sf.read('noti.wav', dtype='float32')  
                      sd.play(data_to_play, fs)
                      status = sd.wait()
                      cookie = driver.get_cookies()
                      ua = driver.execute_script('return navigator.userAgent')
                      num_of_tickets, total_cart = None, None
                      try:
                        num_of_tickets = check_for_element(driver, '#num_of_tickets').text.split(':')[1]
                      except: pass
                      try:
                        total_cart = check_for_element(driver, '#cart >div > div> div> div').text.split('\n')[2]
                      except: pass
                      if not num_of_tickets:
                        try:
                          num_of_tickets = category_amount_dict[random.choice(list(category_amount_dict.keys()))]
                        except: pass
                      print(num_of_tickets, total_cart)
                      
                      full_data = {"type": 1, 'url': driver.current_url, 'name': None, 'date': None, 'city': None,
                        'proxy': proxy, 'cookie': cookie, 'user-agent': ua, 'num_of_tickets': num_of_tickets, 'total_cart': total_cart, 'adspower': data['adspower_number']}
                      try: post_request(full_data)
                      except: print("Can't send message. Slack-bot is off")
                      input('Continue?')
                      break
            limit = False
    except Exception as e:
        print("EXCEPTION", e)
        if reload_time: time.sleep(reload_time)
        else: time.sleep(45)
        


def is_within_range(target, lower_bound, upper_bound):
    print(target, type(target))
    for num in range(lower_bound, upper_bound + 1):
        if num == target: return True
    return False


def process_type_2(link, category_amount_dict, datas, proxy, proxy_url, reload_time):
    driver = selenium_connect(proxy)
    while True:
        try:
            try:
                driver.get(link)
                if wait_for_something(driver, 'button[data-bdd="accept-modal-accept-button"]'):
                    driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="accept-modal-accept-button"]').click()
                driver.find_element(By.XPATH, '//div[text()="Pardon the Interruption"]')
                if proxy_url: change_ip(proxy_url)
                time.sleep(45)
                continue
            except: pass
            try:
                driver.find_element(By.CSS_SELECTOR, 'div[id="t1"]')
                if proxy_url: change_ip(proxy_url)
                time.sleep(45)
                continue
            except: pass
            try:
                driver.find_element(By.CSS_SELECTOR, 'div[class="ToggleSwitch__VisibleToggle-sc-tcnwub-2 hNnBYt"]').click()
            except: pass
            try:
                random_key = random.choice(list(category_amount_dict.keys())).strip()
                driver.find_element(By.CSS_SELECTOR, 'button[class="sc-g9wzf-2 japIkg"]').click()
                driver.find_element(By.XPATH, f'//span[ contains(text(), "{random_key}")]').click()
                driver.find_element(By.XPATH, '//span[ contains(text(), "All Ticket Types")]').click()
                time.sleep(2)
                plus = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tselectionSpinbuttonPlus"]')
                
                print(category_amount_dict)
                if category_amount_dict[random_key]:
                    amount = int(driver.find_element(By.CSS_SELECTOR, 'span[data-testid="tselectionSpinbuttonValue"]').text)
                    for i in range (int(category_amount_dict[random_key]) - amount):
                        try: 
                            if driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tselectionSpinbuttonPlus"][disabled]'): break
                            plus.click()
                        except: pass
                else:
                    while True:
                        try:
                            if driver.find_element(By.CSS_SELECTOR, 'button[data-testid="tselectionSpinbuttonPlus"][disabled]'): break
                            plus.click()
                        except: pass
                if check_for_element(driver, '//div[@data-testid="reserveError"]', xpath=True):
                    if proxy_url: change_ip(proxy_url)
                    time.sleep(45)
                    continue
                if look_for_tickets(driver) and not wait_for_button(driver): 
                    if 'checkout' in driver.current_url:
                        data, fs = sf.read('noti.wav', dtype='float32')  
                        sd.play(data, fs)
                        status = sd.wait()
                        input('Continue?')
            except Exception as e:
                print(e)
                write_error_to_file(e)
        except Exception as e:
            print(e)

# //span[ contains(text(), 'Standard Admission') and @id]
def process_type_3(link, category_amount_dict, datas, proxy, proxy_url, reload_time, time_to_wait, price, levels, accounts, adspower=None, near=None):
    driver = ''
    temp_proxy = proxy if not isinstance(proxy, list) else choice(proxy)
    driver = create_new_connection(temp_proxy, link)
    while True:
        try:
            try:
                driver.get(link)
                if wait_for_something(driver, 'button[data-bdd="accept-modal-accept-button"]'):
                    driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="accept-modal-accept-button"]').click()
                driver.find_element(By.XPATH, '//div[text()="Pardon the Interruption"]')
                if proxy_url: change_ip(proxy_url)
                time.sleep(45)
                continue
            except: pass
            try:
                driver.find_element(By.CSS_SELECTOR, 'div[id="t1"]')
                driver.close()
                driver.quit()
                driver = create_new_connection(temp_proxy, link)
                continue
            except: pass
            try:
                driver.find_element(By.CSS_SELECTOR, '#onetrust-reject-all-handler').click()
            except: pass
            try:
                empty_category = True
                try:
                    if not '' in category_amount_dict.keys(): empty_category = False
                except: pass
                print(empty_category)
                if not empty_category:
                    driver.find_element(By.CSS_SELECTOR, '#edp-quantity-filter-button').click()
                    time.sleep(3)
                    
                    driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="unselectAllTicketTypesBtn"]').click()
                    random_key = random.choice(list(category_amount_dict.keys())).strip()
                    try:
                        driver.find_element(By.XPATH, f"//ul/li/label/span[ contains(text(), '{random_key}')]").click()
                    except:
                        driver.find_element(By.XPATH, f"//span[ contains(text(), '{random_key}') and @id]").click()
                    select_element = driver.find_element(By.CSS_SELECTOR, '#filter-bar-quantity')
                    select = Select(select_element)
                    select.select_by_index(int(category_amount_dict[random_key])-1)
                    driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="applyFilterBtn"]').click()
                
                while True:
                    if wait_for_something(driver, '#quickpicks-listings'):
                        tickets = driver.find_elements(By.CSS_SELECTOR, '#quickpicks-listings > ul > li')

                        # inp = check_for_element(driver, 'input[aria-describedby="label-description-max"]')
                        # inp.send_keys(str(price))
                        ticket_sorted = []
                        for ticket in tickets:
                            # Extract the price attribute
                            ticket_price = ticket.get_attribute("data-price")
                            # Convert the price to a float (remove '$' sign if necessary)
                            ticket_price = float(ticket_price.replace("$", ""))
                            # Append the price and the ticket element to the list
                            ticket_sorted.append((ticket_price, ticket))

                        # Sort the list of ticket prices based on the price
                        ticket_sorted.sort(key=lambda x: x[0])

                        for ticket_price, ticket in ticket_sorted:
                            print(price)
                            print(ticket_price, ticket)
                            if price: 
                                if not ticket_price <= price: continue
                            # while True:
                            #     if levels:
                            #         sec = ticket.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > span').text.split(' • ')[0].split(' ')[1]
                            #         value = is_within_range(int(sec), int(levels[0]), int(levels[-1]))
                            #     else: break
                            #     if not empty_category:
                            #         if value and int(category_amount_dict[random_key]) < 2: continue
                            #         elif value and int(category_amount_dict[random_key]) >= 2: break
                            #         else: break
                            #     else:
                            #         if value and int(category_amount_dict[random.choice(list(category_amount_dict.keys())).strip()]) < 2: continue
                            #         elif value and int(category_amount_dict[random.choice(list(category_amount_dict.keys())).strip()]) >= 2: break
                            #         else: break
                            ticket.click()
                            wait_for_clickable(driver, 'button[data-bdd="offer-card-buy-button"]')
                            total = driver.find_element(By.CSS_SELECTOR, 'div[data-bdd="offer-card-bag"] > div[data-testid="OrderBreakdownTestId"] > div > div >div:nth-child(2)')
                            amount = driver.find_element(By.CSS_SELECTOR, 'div[data-bdd="offer-card-bag"] > div[data-testid="OrderBreakdownTestId"] > div > div:nth-child(2)')
                            total_text, amount_text = None, None
                            if total and amount: 
                                total_text = total.text
                                amount_text = amount.text
                            print(amount_text, total_text)
                            driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="offer-card-buy-button"]').click()
                            modal = wait_for_element(driver, '#modalContent', timeout=5)
                            if modal: modal.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div >button > span').click()
                            temp_account = None
                            WebDriverWait(driver, 30).until(lambda driver: 'checkout' in driver.current_url)
                            if accounts:
                                try:
                                    temp_account = choice(accounts)
                                    check_for_element(driver, 'input[id="email[objectobject]__input"]', click=True).send_keys(temp_account.keys())
                                    check_for_element(driver, 'input[id="password[objectobject]__input"]', click=True).send_keys(temp_account.values())
                                    check_for_element(driver, 'button[data-bdd="sign-in-button"]', click=True)
                                except Exception as e: print(e)
                            print(driver.current_url.split('.')[0])
                            WebDriverWait(driver, 30).until(lambda driver: 'checkout' in driver.current_url.split('.')[0])
                            try:
                                total_text = check_for_element(driver, 'div[data-tid="summary-quantity-type"] > span:nth-child(1)').text + check_for_element(driver, 'div[data-tid="summary-quantity-type"] > span:nth-child(2)')
                                amount_text = check_for_element(driver, 'div[data-tid="summary-price"] > span').text
                            except Exception as e: print(e)
                            while driver.execute_script("return document.readyState") != "complete": pass
                            data, fs = sf.read('noti.wav', dtype='float32')  
                            cookie = driver.get_cookies()
                            ua = driver.execute_script('return navigator.userAgent')
                            sd.play(data, fs)
                            status = sd.wait()
                            if datas: full_data = {"type": 1, 'url': driver.current_url, 'name': datas[0], 'date': datas[1], 'num_of_tickets': amount_text,
                                'total_cart': total_text, 'city': datas[2],'proxy': temp_proxy, 'cookie': cookie, 'user-agent': ua, 'account': temp_account if accounts else ' '}
                            # else: full_data = {"type": 1, 'url': driver.current_url, 'name': 'no name', 'None': 'None', 'city': 'None'}
                            post_request(data=full_data)
                            time.sleep(600)
                            break
                        select.select_by_index(int(category_amount_dict[random_key]))
                        select.select_by_index(int(category_amount_dict[random_key])-1)
            except Exception as e:
                print(e)
                write_error_to_file(e)
        except Exception as e:
            pass


def process_type_4(driver):
    global data
    link = data['link']
    category_amount_dict = data['category_amount_dict']
    reload_time = int(data['refresh_interval'])
    near = data['is_near']

    print(category_amount_dict)
  
    while True:
        try:
            is_queue = wait_for_element(driver, 'aside[aria-label="Seat Map"]')
            if not is_queue: 
                print('waiting for queue')
                time.sleep(5)
            else: break
        except: pass
    # main loop
    while True:
        try:
            driver.refresh()
            # try:
            #     is_queue = wait_for_element(driver, 'div[data-bdd="lobby-queue-tips"]', timeout=5)
            #     print('queue ', is_queue)
            #     if is_queue: queue_bypass(driver, email, password)
            # except: pass
            try:
                check_for_element(driver, '#onetrust-reject-all-handler', click=True)
                driver.find_element(By.XPATH, '//div[text()="Pardon the Interruption"]')
                if reload_time: time.sleep(reload_time)
                else: time.sleep(45)
                driver.refresh()
            except: pass
            try:
                pass
                filters = []
                empty_category = True
                empty_amount = True
                try:
                    if not '' in category_amount_dict.keys(): empty_category = False
                    if not '' in category_amount_dict.values(): empty_amount = False
                except Exception as e: print(e)
                try: 
                    if any('standing' in x.lower() for x in category_amount_dict.keys()): filters.append('standing')
                except: pass
                try:
                    if parse_ranges(category_amount_dict.keys()): filters.append('sectors')
                except: pass
                try: 
                    if any(isinstance(x, str) and 'standing' not in x.lower() for x in category_amount_dict.keys()): filters.append('categories')
                except: pass
                try:
                    if any('standing only' in x.lower() for x in category_amount_dict.keys()): filters.append('standing only')
                except: pass
                our_amount_raw = category_amount_dict[random.choice(list(category_amount_dict.keys()))]
                try:
                    our_amount_raw = int(our_amount_raw)
                except: pass



                if not isinstance(our_amount_raw, int): 
                    our_amount_raw = parse_range(our_amount_raw)
                    print('OUR AMOUNT', our_amount_raw)
                    our_amount = random.randrange(our_amount_raw[0], our_amount_raw[1])
                if not empty_category:
                    if 'standing only' in filters:pass
                    elif 'standing' in filters:
                        categories_list_button = check_for_element(driver, 'div[role="toolbar"] > button:nth-of-type(3)')
                        if categories_list_button.get_attribute('aria-pressed') == "false": categories_list_button.click()
                        time.sleep(1)
                        vip_categories = check_for_element(driver, '//*[@id="list-view"]/div[1]/div[2]/div/div[3]/ul', xpath=True)
                        standard_categories = check_for_element(driver, '//*[@id="list-view"]/div[1]/div[2]/div/div[2]/ul', xpath=True)
                        [click_with_scroll(driver, category) if category is not False else None for category in check_for_elements(standard_categories, ".//*[contains(text(),'Standing')]", xpath=True)]
                        [click_with_scroll(driver, category) if category is not False else None for category in check_for_elements(vip_categories, ".//*[contains(text(),'Standing')]", xpath=True)]
                    if 'categories' in filters:
                        for x in category_amount_dict.keys():
                            if isinstance(x, str) and 'standing' not in x.lower() and not parse_range(x):
                                check_for_element(driver, f"//*[@id=\"quickpicks\"]/div[1]/div[2]/div//span[contains(text(),'{x}')]", xpath=True, click=True)
                print('after break')
                our_amount = 2
                if not empty_amount:
                    tickets_amount_button = check_for_element(driver, 'div[role="toolbar"] > button:nth-of-type(1)')
                    if tickets_amount_button.get_attribute('aria-pressed') == "false": tickets_amount_button.click()
                    time.sleep(1)
                    amount_raw = check_for_element(driver, 'span[data-testid="tselectionSpinbuttonValue"]')
                    amount = None
                    if amount_raw: amount = int(amount_raw.text)
                    print("our amount", our_amount, '\namount', amount)
                    if amount == our_amount: 
                        pass
                    elif amount > our_amount:
                        for _ in range(amount - our_amount):
                            check_for_element(driver, 'button[data-testid="tselectionSpinbuttonPlus"]',click=True, debug=True)
                    elif amount < our_amount:
                        for _ in range(our_amount - amount):
                            check_for_element(driver, 'button[data-testid="tselectionSpinbuttonPlus"]',click=True, debug=True)
                # if price: 
                #     price_arr = parse_range(price)
                #     print(price_arr)
                #     check_for_element(driver, 'div[role="toolbar"] > button:nth-of-type(2)', click=True)
                #     time.sleep(1)
                #     price_element_max = check_for_element(driver, 'input[id="priceSliderFilterInput-max"]')
                #     price_element_max.send_keys(price_arr[1])


                no_reload = False
                for _ in range(3):
                    if not check_for_element(driver, '//span[contains(text(), "Reload the Map")]', click=True): no_reload = True
                if not no_reload:
                    driver.delete_all_cookies()
                    continue
                if 'standing only' in filters:
                    sections_raw = check_for_elements(driver, 'path[data-section-name][data-active="true"][data-section-name="GENERAL ADMISSION - Standing Room Only"]')
                else: sections_raw = check_for_elements(driver, 'path[data-section-name][data-active="true"]')
                if len(sections_raw) < 1: 
                    time.sleep(30)
                    continue
                sections = sections_raw[:len(sections_raw)//2]
                clicked = False
                circles = None
                map_container = None
                # Loop until we find and click a valid section
                while sections:
                    # Select a random section from the remaining list
                    random_section = random.choice(sections)
                    
                    # Remove the selected section from the list to avoid checking it again
                    sections.remove(random_section)

                    try:
                        section_number_raw = random_section.get_attribute('data-section-name')
                        section_number = None

                        # Check if the section name has numbers
                        try: section_number = int(section_number_raw)
                        except: pass
                        if isinstance(section_number, int):
                          # Check if the section number falls within any of the parsed ranges
                          for parsed_range in parse_ranges(category_amount_dict.keys()):
                            print(f"Checking section number: {section_number}, Parsed range: {parsed_range}")
                            if parsed_range[0] < section_number < parsed_range[1]:
                              random_section.click()
                              print('CLICKED: Valid section found')
                              clicked = True
                              break  # Break out of the for loop after successful click
                          if clicked:
                            break  # Break out of the while loop after successful click
                        else:
                            
                          # If the section doesn't contain numbers, click on it
                          try:  random_section.click()
                          except: coordinate_click(driver, random_section)
                          print("CLICKED: Section without numbers")
                          clicked = True
                          break  # Exit the while loop after successful click

                    except Exception as e:
                      print(f"Error occurred: {e}")
                      time.sleep(5)  # Wait before retrying
                      continue  # Retry with the next section
                # If no sections were found and clicked
                if not clicked:
                  print("No valid section found.")
                
                # After clicking, proceed with your wait
                
                if clicked:
                    time.sleep(2)
                    circles = check_for_elements(driver, 'circle[type="primary"]')
                    map_container = check_for_element(driver, 'div[id="map-container"] > div[data-component="tooltip"]')
                nearby_enough = True
                print(map_container)
                # FOR SEATED
                if not 'standing only' in filters:
                    if circles:
                        print('CIRCLES')
                        if len(circles) < our_amount: continue
                        elif len(circles) >= our_amount and not near:
                            for circle in circles:
                                try: circle.click()
                                except: pass
                        elif len(circles) >= our_amount and near:
                            circle = random.choice(circles)
                            x = float(circle.get_attribute('cx'))
                            is_nearby = check_nearby_tickets(driver, x, our_amount)
                            print('is_nearby', is_nearby)
                            nearby_enough = is_nearby

                        if not nearby_enough: continue
                        elif nearby_enough:
                            tickets = check_for_elements(driver, '//*[@id="list-view"]/div/div[2]/ul/div', xpath=True)
                            if int(tickets.text) >= our_amount: 
                                wait_for_element(driver, 'button[data-bdd="offer-card-buy-button"]', click=True)
                                time.sleep(2)
                                no_tickets = wait_for_element(driver, 'div[aria-labelledby="noAvailabilityLabel"]', timeout=15)
                                if no_tickets: continue
                        
                # FOR STANDING
                if map_container:
                    print('MAP CONTAINER')
                    tickets = check_for_elements(driver, '#map-container div[data-testid="ticketTypeInfo"]')
                    for _ in range(2): 
                        minus_button = check_for_element(tickets[0], 'button[data-testid="tselectionSpinbuttonMinus"]')
                        if minus_button: minus_button.click()

                    random_ticket = random.choice(tickets)
                    for _ in range(our_amount):
                        plus_button = check_for_element(random_ticket, 'button[data-testid="tselectionSpinbuttonPlus"]')
                        if plus_button: plus_button.click()

                    check_for_element(driver, 'button[data-testid="gaToolTipBtn"]', click=True)
                    wait_for_element(driver, 'button[data-bdd="offer-card-buy-button"]', click=True)
                    time.sleep(2)
                    no_tickets = wait_for_element(driver, 'div[aria-labelledby="noAvailabilityLabel"]', timeout=15)
                    if no_tickets: continue
                
                if not map_container and not circles: continue

                # IF SUCCESS
                success = wait_for_element(driver, 'form[action="/checkout/order"]', timeout=60, click=True)
                if success:
                  data_to_play, fs = sf.read('noti.wav', dtype='float32')
                  sd.play(data_to_play, fs)
                  status = sd.wait()

                  total = check_for_element(driver, 'span[data-bdd="order-summary-ticket-quantity"]')
                  data_to_send = f'*Усього квитків:* {total.text}\n'
                  unit_1 = check_for_element(driver, 'span[data-bdd="order-summary-ticket-facevalue"]')
                  
                  event_name = check_for_element(driver, 'h2[class="event-header__title event-header__title--timer truncate-text"]')
                  event_date = check_for_element(driver, 'span[class="event-header__date--timer truncate-text event-header__date"]')
                  event_city = check_for_element(driver, 'span[class="event-header__venue-name event-header__venue-name--timer truncate-text"]')

                  summary = check_for_element(driver, 'div[data-bdd="order-summary-ticket-price"]')
                  event_category = check_for_element(driver, 'span[data-bdd="order-summary-ticket-type"]')

                  data_to_send += f'*Event:* {event_name.text}*\n*Date:* {event_date.text}\n*City:* {event_city.text}\n*Category:* {event_category.text}\n*1 Ticket price:* {unit_1.text}\n*Summary:* {summary.text}\n\n'
                  data_to_send += f'*Url:* {driver.current_url}'
                  post_request({"data": data_to_send, "adspower_api": data['adspower_api'], "adspower_number": data['adspower_number']}, '/adspower')
                  time.sleep(600)
                  break

            except Exception as e: print(e)
        except Exception as e:
            print(e)


def click_with_scroll(driver, element, debug=False):
    try:
        driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()
        time.sleep(.5)
        return True
    except Exception as e:
        if debug: print(e)
        return False
    

def coordinate_click(driver, element):
    for _ in range(10):
      print('try to click')
      try:
        location = element.location  # {'x': x_position, 'y': y_position}
        size = element.size  # {'width': width, 'height': height}
        print(location, size)

        # Calculate the bounding box (top-left and bottom-right positions)
        x1 = int(location['x'])
        y1 = int(location['y'])
        x2 = x1 + int(size['width'])
        y2 = y1 + int(size['height'])
        
        # Generate a random x, y within the bounding box
        random_x = random.randint(x1, x2)
        random_y = random.randint(y1, y2)

        # Perform the click at the random coordinates
        actions = ActionChains(driver)
        actions.move_by_offset(random_x, random_y).click().perform()
        return True
      except Exception as e: 
        print('coordinate_click function exception', e)
        continue

from selenium.common.exceptions import StaleElementReferenceException

def check_nearby_tickets(driver, x, aim_amount, temp_amount=1, visited=None):
    try:
    # Initialize the set to keep track of visited elements
        if visited is None:
            visited = set()

        # Add the current circle's x-coordinate to the visited set
        visited.add(x)

        # Find nearby elements by x, excluding the current one and already visited elements
        print('before error')
        nearby_x = check_for_elements(driver, f'//*[@cx >= {x-20} and @cx <= {x+20} and @cx != {x} and @type="primary"]', xpath=True)
        print('after error')
        # Filter out circles that have already been visited
        nearby_x = [elem for elem in nearby_x if float(elem.get_attribute('cx')) not in visited]

        # Debugging: print how many elements are found and the current temp_amount
        print(f"Temp Amount: {temp_amount}, Nearby X: {len(nearby_x)}, Visited: {visited}")
        
        # Base case: if the target amount has been reached
        if aim_amount <= temp_amount:
            return True

        # If there are no more nearby elements to check, return False
        if not nearby_x:
            print("No more nearby tickets, returning False.")
            return False

        # Recursive case: Check nearby circles by x coordinates
        if nearby_x:
            # Click on the first nearby x circle before recursion
            loop_click(driver, nearby_x[0])
            cx = nearby_x[0].get_attribute('cx')

            if check_nearby_tickets(driver, cx, aim_amount, temp_amount + 1, visited):
                return True  # If recursion succeeds, return True

        # No valid nearby tickets left that meet the condition
        print("Exhausted nearby tickets, returning False.")
        return False
    except StaleElementReferenceException: 
        nearby_x = check_for_elements(driver, f'//*[@cx >= {x-20} and @cx <= {x+20} and @cx != {x} and @type="primary"]', xpath=True)
        nearby_x = [e for e in nearby_x if float(e.get_attribute('cx')) not in visited]
    except Exception as e: print('Exception in check_nearby_tickets function.', e)


def loop_click(driver, nearby_x):
  temp_cx = None
  temp_cy = None
  while True:
    try:
      temp_cx = nearby_x.get_attribute('cx')
      temp_cy = nearby_x.get_attribute('cy')
      print('before stale')
      nearby_x.click()
      return True
    except StaleElementReferenceException:
      print('stale')
      stale_nearby = check_for_element(driver, f'//*[@cx == {temp_cx} and @cy == {temp_cy}]', xpath=True)
      stale_nearby.click()
      return True
    except Exception as e: 
      print('Exception in loop_click function.', e)
      time.sleep(10)
      return False


def parse_range(s):
    # Regular expression to match the pattern "min-max" where min and max are positive integers
    pattern = r"^(\d+)-(\d+)$"
    
    # Search for matches
    match = re.match(pattern, s)
    
    if match:
        # Convert the matched groups to integers
        min_val = int(match.group(1))
        max_val = int(match.group(2))
        
        # Ensure that min is less than or equal to max
        if min_val <= max_val:
            return [min_val, max_val]
    
    # Return None if the input is invalid or out of range
    return None
    

def parse_ranges(strings):
    # Process each string in the list using parse_range
    return [parse_range(s) for s in strings if parse_range(s) is not None]


def has_words(inputString):
    # Check if there's at least one sequence of alphabetic characters in the string
    return any(word.isalpha() for word in re.findall(r'\b\w+\b', inputString))


def check_model():
  while True:
    model = input("Choose model:\n0  Client Model [DEFAULT]\n1  Server Model\n--> ")
    
    if model == '0' or model == '1' or model == '':
      # If empty string, set model to '0'
      if model == '':
        model = '0'
      return model
    else:
        print("Invalid input. Please enter '0', '1', or leave it blank for default (0).")

def safe_list_get (l, idx):
  try:
    return l[idx]
  except IndexError:
    return None
  

def is_port_open(host, port):
  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.connect((host, port))
    return True
  except (socket.timeout, ConnectionRefusedError):
    return False
  finally:
    sock.close()


data = {
    'link': '',
    'category_amount_dict': {},
    'price': ['0-999'],
    'is_near': False,
    'refresh_interval': 30,
    'adspower_number': '',
    'adspower_api': '',
    'proxy': '',
    'invitation_code': ''
}


@eel.expose
def main(link, categoryAmountDict, price, isNear, refreshInterval, adspowerNumber=None, adspowerAPI=None, proxy=None, invitationCode=None):
    global data
    data.update({
        'link': link,
        'category_amount_dict': categoryAmountDict,
        'price': price,
        'is_near': isNear,
        'refresh_interval': refreshInterval,
        'adspower_number': adspowerNumber,
        'adspower_api': adspowerAPI,
        'proxy': proxy,
        'invitation_code': invitationCode
    })
    print(data)
    eel.spawn(run)


@eel.expose
def restart_main(link, categoryAmountDict, price, isNear, refreshInterval, adspowerNumber=None, adspowerAPI=None, proxy=None, invitationCode=None):
    print("Restarting the process...")
    global data
    data.update({
        'link': link,
        'category_amount_dict': categoryAmountDict,
        'price': price,
        'is_near': isNear,
        'refresh_interval': refreshInterval,
        'adspower_number': adspowerNumber,
        'adspower_api': adspowerAPI,
        'proxy': proxy,
        'invitation_code': invitationCode
    })
    print(data)
    print("Process restarted.")


def run():
    global data
    adspower_api = data['adspower_api']
    proxy = data['proxy']
    
    # Connecting to selenium based on adspower/proxy data
    if not adspower_api:
        temp_proxy = 'vpn'
        if proxy != 'vpn': temp_proxy = proxy
        driver = create_new_connection(temp_proxy, data['link'])
        time.sleep(2)
        if proxy == 'vpn':
            tabs = driver.window_handles
            driver.switch_to.window(tabs[1])
            driver.close()
            driver.switch_to.window(tabs[0])
            reconnect_vpn(driver, data['link'])
    elif adspower_api:
        driver = selenium_connect(proxy, adspower_api, data['adspower_number'])
    
    # Ensure driver is initialized before using it
    if driver:
        driver.get(data['link'])
    else:
        print("Driver initialization failed")

    # main code goes here
    while True:
      if check_for_element(driver, 'aside[aria-label="Seat Map"]'):
          check_for_element(driver, '//aside[@aria-label="Seat Map"]/div[1]/button[2]', xpath=True, click=True)
          if wait_for_element(driver, '//h2[contains(text(), "Search For Tickets")]', xpath=True, timeout=5) or wait_for_element(driver, '#main-content', timeout=5):
              process_type_1(driver)
          # elif wait_for_element(driver, 'div[id="quickpicks"]l', timeout=5):
          #   process_type_2(driver)
          # elif wait_for_element(driver, '#map-container', timeout=5):
          #   process_type_4(driver)


if __name__ == "__main__":
    selected_model = check_model()
    if selected_model == '0':
        eel.init('web')

        port = 8000
        while True:
            try:
                if not is_port_open('localhost', port):
                    eel.start('main.html', size=(700, 800), port=port)
                    break
                else:
                    port += 1
            except OSError as e:
                print(e)
    elif selected_model == '1':
        data = get_data_from_google_sheets()
        threads = []
        for row in data:
            near = row[0]
            link = row[6]
            types = int(row[1])
            categories = row[2].split('\n')
            
            amounts = row[3].split('\n')
            print(amounts)
            price, levels = None, None
            try:
                price = row[4]
                levels = row[5].split('\n')[0].split(' ')
            except: pass
            data = [row[7], row[8], row[9]]
            proxy, proxy_url, reload_time, time_to_wait, adspower, email, password = None, None, None, None, None, None, None
            try: 
                proxy = row[10] 
                proxy_list = ''
                if ' ' in proxy: proxy_list = proxy.split(' ')
                proxy_url = row[11]
            except: pass
            try:
                adspower = row[14]
            except: pass
            try:
                email = row[15]
                password = row[16]
                print(email, password)
            except: pass
            try: reload_time = int(row[12])
            except Exception as e: print('Введіть reload_time в числовому форматі', e)
            try: time_to_wait = int(row[13])
            except Exception as e: print('Введіть time_to_wait в числовому форматі', e)
            # try:
            #     accounts_raw = row[14]
            #     accounts = [{account.split(':')[0]: account.split(':')[1]} for account in accounts_raw.split(' ')]
            # except Exception as e: print(e)
            category_amount_dict = {}
            if len(amounts) == 1 and len(categories) > 1:
                for category in categories:
                    category_amount_dict[category.strip()] = amounts[0].strip()
            else:
                for category, amount in zip(categories, amounts):
                    category_amount_dict[category.strip()] = amount.strip()
                    
            print(category_amount_dict)
            process_link = None
            if types == 1: process_link = process_type_1
            elif types == 2: process_link = process_type_1
            elif types == 3: process_link = process_type_3
            elif types == 4: process_link = process_type_4 
            thread = threading.Thread(target=process_link, args=(link, category_amount_dict, data, 
            proxy if not proxy_list else proxy_list, proxy_url, reload_time, time_to_wait, price, levels, email, password, adspower, near))
            thread.start()
            threads.append(thread)

            delay = random.uniform(5, 10)
            time.sleep(delay)
        
        for thread in threads:
            thread.join()
        