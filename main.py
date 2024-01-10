import requests
import time
import re
import sys, os
import json
import pandas as pd
from selenium.webdriver.common.by import By
import undetected_chromedriver as webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import shutil
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


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = '15aFBq6GSuaF8L6dFsA4Aw141dQy2s6N_MKZHgvpdSjo'


PROXY = ('proxy.packetstream.io', 31112, 'pergfan', '6ofKZOXwL7qSTGNZ_country-France')

R_TABLE = {}

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


def selenium_connect(proxy):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    #options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--lang=EN')
    if proxy:
        proxy = proxy.split(':')
        proxy[1] = int(proxy[1])
        proxy_extension = ProxyExtension(*proxy)
        options.add_argument(f"--load-extension={proxy_extension.directory}")

    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)


    # Create the WebDriver with the configured ChromeOptions
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
    set_random_16_9_resolution(driver)

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
        range_name = "main!A2:J"

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
    price_without_euro_each = raw_price.replace('€', '').replace(' each', '').strip()

    if '–' in price_without_euro_each:
        right_part = re.split(r'–', price_without_euro_each)[-1]
        processed_price_str = right_part
    else:
        processed_price_str = price_without_euro_each

    processed_price_str = processed_price_str.replace(',', '.')

    processed_price = float(processed_price_str)
    if processed_price.is_integer():
        return int(processed_price)
    else:
        return processed_price


def wait_for_button(driver):
    try:
        if WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="reserveError"]'))):
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


def write_error_to_file(error_message):
    with open('error_log.txt', 'a') as file:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        file.write(f'{timestamp}: {error_message}\n')


def send_cookies(driver):
    cookies = driver.get_cookies()
    cookies_json = json.dumps(cookies)
    return cookies_json


def post_request(data):
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
        response = requests.post("http://localhost:808/book", data=json_data, headers=headers)
        print(response)
    except Exception as e:
        print(e)
    # Check the response status code
    if response.status_code == 200:
        print("POST request successful!")
    else:
        print("POST request failed.")


def check_for_element(driver, selector, click=False, xpath=False):
    try:
        if xpath:
            element = driver.find_element(By.XPATH, selector)
        else:
            element = driver.find_element(By.CSS_SELECTOR, selector)
        if click: 
            driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
        return element
    except: return False


def change_ip(url):
    try:
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # You can print the response content or return it as needed
            # For example, printing the response content:
            print(response.text)
        else:
            print(f"Request failed with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def process_type_1(link, category_amount_dict, datas, proxy, proxy_url):
  driver = selenium_connect(proxy)
  while True:
    try:
        driver.get(link)
        action_chains = ActionChains(driver)
        for _ in range(5): action_chains.key_down(Keys.CONTROL).send_keys(Keys.SUBTRACT).key_up(Keys.CONTROL)
        action_chains.perform()
        try:
            wait_for_clickable(driver, '#onetrust-reject-all-handler')
            driver.find_element(By.CSS_SELECTOR, '#onetrust-reject-all-handler').click()
            driver.find_element(By.XPATH, '//div[text()="Pardon the Interruption"]')
            if proxy_url: change_ip(proxy_url)
            print('waiting for 45 sec')
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
            driver.find_elements(By.CSS_SELECTOR, 'button[class="sc-aitciz-1 hWHZkc"]')[1].click()
        except: print("did not manage to click on 'Find seats for me'")
        # try:
        #     driver.find_element(By.CSS_SELECTOR, 'svg[class="BaseSvg-sc-yh8lnd-0 MagnifyingGlassIcon___StyledBaseSvg-sc-1pooy9n-0 ckLyyv"]').click()
        # except: pass
        ticket_data = {}
        tickets = driver.find_elements(By.CSS_SELECTOR, 'ul[class="sc-krebt0-0 dQKSqi"] > li')
        
        for ticket in tickets:
            category = ticket.find_element(By.CSS_SELECTOR, 'span[class="sc-148tjjv-3 izkONI"]').text.split('\n')[0]
            # price = extract_price(ticket.find_element(By.CSS_SELECTOR, 'span[class="sc-148tjjv-5 chohwl"]').text)
            ticket_data[category] = {"ticket": ticket}
        limit = True
        while limit:
            if ticket_data:
                # Randomly choose a key from ticket_data
                while True:
                    random_key = choice(list(ticket_data.keys()))
                    if len(category_amount_dict) == 0: break
                    if len(category_amount_dict) == 1 and list(category_amount_dict.keys())[0] == '': break
                    if random_key not in category_amount_dict.keys(): continue
                    break
                
                # Process the selected entry
                selected_entry = ticket_data[random_key]
                ticket = selected_entry['ticket']
                plus = ticket.find_element(By.CSS_SELECTOR, 'button[data-testid="tselectionSpinbuttonPlus"]')
                if len(category_amount_dict) == 1 and list(category_amount_dict.keys())[0] == '':
                    if category_amount_dict['']:
                        amount = int(ticket.find_element(By.CSS_SELECTOR, 'span[data-testid="tselectionSpinbuttonValue"]').text)
                        for i in range (int(category_amount_dict['']) - amount):
                            try: 
                                plus.click()
                                if driver.find_element(By.CSS_SELECTOR, 'p[data-testid="ticketLimitMsg"]'): break
                            except: pass
                    else:
                        while True:
                            try: 
                                plus.click()
                                if driver.find_element(By.CSS_SELECTOR, 'p[data-testid="ticketLimitMsg"]'): break
                            except: pass
                elif category_amount_dict[random_key]:
                    amount = int(ticket.find_element(By.CSS_SELECTOR, 'span[data-testid="tselectionSpinbuttonValue"]').text)
                    for i in range (int(category_amount_dict[random_key]) - amount):
                        try: 
                            plus.click()
                            if driver.find_element(By.CSS_SELECTOR, 'p[data-testid="ticketLimitMsg"]'): break
                        except: pass
                
                else:
                    while True:
                        try: 
                            plus.click()
                            if driver.find_element(By.CSS_SELECTOR, 'p[data-testid="ticketLimitMsg"]'): break
                        except: pass

                while True:
                    check_for_element(driver, 'button[data-testid="findTicketsBtn"]', click=True)
                    wait_for_button(driver)
                    if check_for_element(driver, '//div[@data-testid="reserveError"]/*[contains(text(), "Something went wrong...")]', xpath=True):
                        driver.delete_all_cookies()
                        set_random_16_9_resolution(driver)
                        break
                    if look_for_tickets(driver): 
                        if 'checkout' in driver.current_url:
                            data, fs = sf.read('noti.wav', dtype='float32')  
                            sd.play(data, fs)
                            status = sd.wait()
                            if datas: full_data = {"type": 1, 'url': driver.current_url, 'name': datas[0], 'date': datas[1], 'city': datas[2]}
                            else: full_data = {"type": 1, 'url': driver.current_url, 'name': 'no name', 'None': 'None', 'city': 'None'}
                            try: post_request(full_data)
                            except: print("Can't send message. Slack-bot is off")
                            input('Continue?')
                            break
                print('exited loop')
            limit = False
    except Exception as e:
        print(e)

# temporary not working!
def process_type_2(link, category_amount_dict, datas, proxy, proxy_url):
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
def process_type_3(link, category_amount_dict, datas, proxy, proxy_url):
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
                driver.find_element(By.CSS_SELECTOR, '#onetrust-reject-all-handler').click()
            except: pass
            try:
                driver.find_element(By.CSS_SELECTOR, '#edp-quantity-filter-button').click()
                time.sleep(3)
                # driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="unselectAllTicketTypesBtn"]').click()
                random_key = random.choice(list(category_amount_dict.keys())).strip()
                driver.find_element(By.XPATH, f"//span[ contains(text(), '{random_key}') and @id]").click()
                select_element = driver.find_element(By.CSS_SELECTOR, '#filter-bar-quantity')
                select = Select(select_element)
                select.select_by_index(int(category_amount_dict[random_key])-1)
                driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="applyFilterBtn"]').click()
                while True:
                    if wait_for_something(driver, '#quickpicks-listings'):
                        tickets = driver.find_elements(By.CSS_SELECTOR, 'li[class="quick-picks__list-item"]')
                        random.choice(tickets).click()
                        wait_for_clickable(driver, 'button[data-bdd="offer-card-buy-button"]')
                        driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="offer-card-buy-button"]').click()
                        WebDriverWait(driver, 30).until(lambda driver: 'checkout' in driver.current_url)
                        data, fs = sf.read('noti.wav', dtype='float32')  
                        sd.play(data, fs)
                        status = sd.wait()
                        if datas: full_data = {"type": 3, 'url': driver.current_url, 'name': datas[0], 'date': datas[1], 'city': datas[2]}
                        else: full_data = {"type": 3, 'url': driver.current_url, 'name': 'no name', 'None': 'None', 'city': 'None'}
                        post_request(full_data)
                        input('Continue?\n')
                        break
                    select.select_by_index(int(category_amount_dict[random_key]))
                    select.select_by_index(int(category_amount_dict[random_key])-1)
            except Exception as e:
                write_error_to_file(e)
        except Exception as e:
            print(e)
        

if __name__ == "__main__":
  data = get_data_from_google_sheets()
  threads = []
  for row in data:
    link = row[4]
    types = int(row[1])
    categories = row[2].split('\n')
    amounts = row[3].split('\n')
    data = [row[5], row[6], row[7]]
    proxy, proxy_url = None, None
    try: 
        proxy = row[8] 
        proxy_url = row[9]
    except: pass

    category_amount_dict = {}
    for category, amount in zip(categories, amounts):
        category_amount_dict[category.strip()] = amount.strip()
    process_link = None
    if types == 1: process_link = process_type_1
    elif types == 2: process_link = process_type_1
    elif types == 3: process_link = process_type_3
    thread = threading.Thread(target=process_link, args=(link, category_amount_dict, data, proxy, proxy_url))
    thread.start()
    threads.append(thread)

    delay = random.uniform(5, 10)
    time.sleep(delay)
  
  for thread in threads:
    thread.join()
  