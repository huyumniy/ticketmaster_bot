import selenium
import random
import time
import os,sys
from selenium.webdriver.common.by import By
import undetected_chromedriver as webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil,tempfile


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
    print(proxy)
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
    else: options.add_argument(f"--load-extension={extension},{extension2}")

    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        options=options,
        enable_cdp_events=True
    )


    return driver

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

def reconnect_vpn(driver, link):
    blacklist = ['Iran', 'Egypt', 'Italy']
    while True:
        try:
            driver.get('chrome-extension://ppaljmgnemghjjciljkbdnebehoddnjc/popup/index.html')
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
                element_text = driver.execute_script("return arguments[0].textContent;", element)
                print(element_text)
                if element_text not in blacklist: break
            driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
            time.sleep(5)
            driver.get(link)
            break
        except Exception as e: pass


if __name__ == "__main__":
    driver = selenium_connect('')
    driver.get('https://www.geeksforgeeks.org/how-to-get-text-of-a-tag-in-selenium-python/')
    reconnect_vpn(driver, 'https://www.geeksforgeeks.org/how-to-get-text-of-a-tag-in-selenium-python/')
    time.sleep(10)