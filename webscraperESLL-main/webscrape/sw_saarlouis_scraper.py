import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")



def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def get_sw_saarlouis_data():

    url = 'https://www.swsls.de/tarifergebnisse?type=Strom&consumption=2500'
    try:
        response = requests.get(url)
        response.raise_for_status() 

        soup = BeautifulSoup(response.text, 'html.parser')

        arbeitspreis = soup.select("#tariff-results > div > div > div > div > div.tariff-results__drawer > div:nth-child(2) > div.copy.copy--small.tariff__prices > div:nth-child(3) > div.price__value")
        ap = transform_number(arbeitspreis[0].text.strip())
        grundpreis = soup.select("#tariff-results > div > div > div > div > div.tariff-results__drawer > div:nth-child(2) > div.copy.copy--small.tariff__prices > div:nth-child(2) > div.price__value")
        gp = transform_number(grundpreis[0].text.strip())
        jp= round(gp * 12 + (ap/100) * 2500, 2)

        return [("SW Saarlouis Avanza", "66740", ap, gp , jp, "Strom")]
    
    except Exception as e:
        logging.exception(f"SW SLS scraper failed {e}")
    return None



def get_sw_saarlouis_gas():
    
    url = "https://www.swsls.de/tarifergebnisse?type=Erdgas&consumption=18000&nominal-output=25"
    try:
        response = requests.get(url)
        response.raise_for_status() 

        soup = BeautifulSoup(response.text, 'html.parser')

        arbeitspreis = soup.select("#tariff-results > div > div > div > div > div.tariff-results__drawer > div:nth-child(2) > div.copy.copy--small.tariff__prices > div:nth-child(3) > div.price__value")
        ap = transform_number(arbeitspreis[0].text.strip())
        grundpreis = soup.select("#tariff-results > div > div > div > div > div.tariff-results__drawer > div:nth-child(2) > div.copy.copy--small.tariff__prices > div:nth-child(2) > div.price__value")
        gp = transform_number(grundpreis[0].text.strip())
        jp= round(gp * 12 + (ap/100) * 2500, 2)

        return [("SW SLS Saarlouiser Erdgas", "66740", ap, gp , jp, "Gas")]
    
    except Exception as e:
        logging.exception(f"SW SLS scraper failed {e}")
    return None



def transform_number(response):
    match = re.search(r"[\d\.]+,\d+", response)
    if match:
        number_str = match.group()
        number_str = number_str.replace(".", "").replace(",", ".")
        return float(number_str)
    else:   
        logging.error("Failed on regex")
        return None
    
if __name__ == "__main__":
    #print(get_sw_saarlouis_data())
    print(get_sw_saarlouis_gas())