import requests
import time
import re
import eel
import sys, os
import json
import pandas as pd
from colorama import init, Fore
from selenium.webdriver.common.by import By
import undetected_chromedriver as webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
init(autoreset=True)  # Initialize colorama for automatic color reset

PROXY = ('proxy.packetstream.io', 31112, 'pergfan', '6ofKZOXwL7qSTGNZ')

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

        background_js = self.background_js % (host, int(port), user, password)
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
    #pergfan:6ofKZOXwL7qSTGNZ@proxy.packetstream.io:31112
    # with open('proxies.txt', "r") as file:
    #     lines = file.readlines()

    # random_line = choice(lines)
    # random_line = random_line.strip()
    # host, port, user, password = random_line.split(":")
    # print("Host:", host)
    # print("Port:", port)
    # print("User:", user)
    # print("Password:", password)
    # proxy = (host, int(port), user, password)
    proxy = proxy.split(':')
    proxy_extension = ProxyExtension(*proxy)
    options.add_argument(f"--load-extension={proxy_extension.directory}")

    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)


    # Create the WebDriver with the configured ChromeOptions
    driver = webdriver.Chrome(
        options=options,
        enable_cdp_events=True,
        driver_executable_path='./chromedriver.exe'
    )

    screen_width, screen_height = driver.execute_script(
        "return [window.screen.width, window.screen.height];")
    
    desired_width = int(screen_width / 2)
    desired_height = int(screen_height / 3)
    driver.set_window_position(0, 0)
    driver.set_window_size(desired_width, screen_height)

    return driver


def print_colored(text, color, rest):
    print(f"{color}[{time.strftime('%H:%M:%S')}]{color}[{text}] {Fore.YELLOW}{rest}")


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
        range_name = "main!A2:H"

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
        print_colored('ERROR', Fore.RED, 'Гугл токен застарiв, звернiться до Влада, щоб вiн його оновив!')
        return None


def extract_price(raw_price):
    price_without_euro_each = raw_price.replace('€', '').replace(' each', '').strip()

    if '–' in price_without_euro_each:  # Use an en dash here (–) instead of a hyphen (-)
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
            driver.find_element(By.CSS_SELECTOR, 'span[class="indexstyles__Text-sc-83qv1q-2 dbVWpK"]').click()
            return True
    except:
        return False

def look_for_tickets(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, 'button[data-testid="findTicketsBtn"]').click()
        return True
    except: return False


def wait_for_something(driver, selector):
    try:
        if WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector))):
            return True
    except: return False


def wait_for_clickable(driver, selector):
    try:
        if WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))):
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


def check_for_element(driver, selector, click=False):
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        if click: element.click()
        return element
    except: return False


def wait_for_queue(driver):
    while True:
        try:
            check_for_element(driver, "//*[contains(text(), 'Get a new place in the queue')]", click=True)
            
            return True
        except: pass


def process_type_1(link, category_amount_dict, datas, proxy):
  driver = selenium_connect(proxy)
  while True:
    driver.get(link)

    try:
        driver.find_element(By.CSS_SELECTOR, '#challenge-container')
        wait_for_queue(driver)
    except: pass
    try:
        wait_for_clickable(driver, '#onetrust-reject-all-handler')
        driver.find_element(By.CSS_SELECTOR, '#onetrust-reject-all-handler').click()
        driver.find_element(By.XPATH, '//div[text()="Pardon the Interruption"]')
        time.sleep(15)
        continue
    except: pass
    try:
      driver.find_elements(By.CSS_SELECTOR, 'button[class="sc-aitciz-1 hWHZkc"]')[1].click()
    except: pass
    try:
      driver.find_element(By.CSS_SELECTOR, 'svg[class="BaseSvg-sc-yh8lnd-0 MagnifyingGlassIcon___StyledBaseSvg-sc-1pooy9n-0 ckLyyv"]').click()
    except: pass
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
                if random_key not in category_amount_dict.keys(): continue
                break

            # Process the selected entry
            selected_entry = ticket_data[random_key]
            ticket = selected_entry['ticket']
            plus = ticket.find_element(By.CSS_SELECTOR, 'button[data-testid="tselectionSpinbuttonPlus"]')
            if category_amount_dict[random_key]:
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

            if look_for_tickets(driver) and not wait_for_button(driver): 
                if 'checkout' in driver.current_url:
                    data, fs = sf.read('noti.wav', dtype='float32')  
                    sd.play(data, fs)
                    status = sd.wait()
                    if datas: full_data = {"type": 1, 'url': driver.current_url, 'name': datas[0], 'date': datas[1], 'city': datas[2]}
                    else: full_data = {"type": 1, 'url': driver.current_url, 'name': 'no name', 'None': 'None', 'city': 'None'}
                    post_request(full_data)
                    input('Continue?')
        limit = False

# temporary not working!
def process_type_2(link, category_amount_dict, datas, proxy):
    driver = selenium_connect(proxy)
    while True:
        try:
            driver.get(link)
            if wait_for_something(driver, 'button[data-bdd="accept-modal-accept-button"]'):
                driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="accept-modal-accept-button"]').click()
            driver.find_element(By.XPATH, '//div[text()="Pardon the Interruption"]')
            time.sleep(15)
            continue
        except: pass
        try:
            driver.find_element(By.CSS_SELECTOR, 'div[class="ToggleSwitch__VisibleToggle-sc-tcnwub-2 hNnBYt"]').click()
        except: pass
        try:
            random_key = random.choice(list(category_amount_dict.keys())).strip()
            print(random_key)
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
            if look_for_tickets(driver) and not wait_for_button(driver): 
                if 'checkout' in driver.current_url:
                    data, fs = sf.read('noti.wav', dtype='float32')  
                    sd.play(data, fs)
                    status = sd.wait()
                    input('Continue?')
        except Exception as e:
            print(e)
            write_error_to_file(e)


# //span[ contains(text(), 'Standard Admission') and @id]
def process_type_3(link, category_amount_dict, datas, proxy):
    driver = selenium_connect(proxy)
    while True:
        try:
            driver.get(link)
            if wait_for_something(driver, 'button[data-bdd="accept-modal-accept-button"]'):
                driver.find_element(By.CSS_SELECTOR, 'button[data-bdd="accept-modal-accept-button"]').click()
            driver.find_element(By.XPATH, '//div[text()="Pardon the Interruption"]')
            time.sleep(15)
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
        
@eel.expose
def main(proxy):
    data = get_data_from_google_sheets()
    if not data: exit()
    threads = []
    for row in data:
        link = row[4]
        types = int(row[1])
        categories = row[2].split('\n')
        amounts = row[3].split('\n')
        name, date, city = None, None, None
        try: name = row[5]
        except: pass
        try: date = row[6]
        except: pass
        try: city = row[7]
        except: pass
        data = [name, date, city]

        category_amount_dict = {}
        for category, amount in zip(categories, amounts):
            category_amount_dict[category.strip()] = amount.strip()
        process_link = None
        if types == 1: process_link = process_type_1
        elif types == 3: process_link = process_type_3
        thread = threading.Thread(target=process_link, args=(link, category_amount_dict, data, proxy))
        thread.start()
        threads.append(thread)

        delay = random.uniform(5, 10)
        time.sleep(delay)
  
    for thread in threads:
        thread.join()
  


if __name__ == "__main__":
  eel.init('web')
  eel.start('main.html', size=(600, 800))