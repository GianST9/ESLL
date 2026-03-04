import os
import sys
import time
import re
import logging
import seleniumwire
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_ca_cert_path():
    """
    Return the correct path to seleniumwire's ca.crt.
    Works both when running as a script or a PyInstaller exe.
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(seleniumwire.__file__)
    return os.path.join(base_path, 'seleniumwire', 'ca.crt')


def get_bearer_token():
    ca_cert_path = get_ca_cert_path()
    logging.info(f"Using CA cert at: {ca_cert_path}")

    seleniumwire_options = {
        'ca_cert_path': ca_cert_path
    }

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")

    driver = webdriver.Chrome(seleniumwire_options=seleniumwire_options, options=chrome_options)

    url = "https://my-stadtwerk.de/"

    try:
        logging.info(f"Navigating to {url}")
        driver.get(url)
        time.sleep(5)  # adjust if necessary

        token = None
        for request in driver.requests:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                logging.info(f"Found Authorization header")
                tokens = re.findall(r'Bearer ([A-Za-z0-9\-._~+/]+=*)', auth_header)
                if tokens:
                    token = tokens[-1]
                    #logging.info(f"Extracted Bearer token: {token}")
                    break

        if not token:
            logging.warning("No Bearer token found in the requests.")

        return token

    except Exception as e:
        logging.exception(f"Bearer Token extraction failed: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    token = get_bearer_token()
    if token:
        print(f"Bearer Token: {token}")
    else:
        print("Bearer Token not found.")