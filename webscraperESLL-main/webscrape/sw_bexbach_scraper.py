import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_sw_bexback_data():

    url = "https://www.stadtwerke-bexbach.de/de/Privatkunden/Strom/Preise-und-Tarife-Oekostrom/"
    
    options = Options()
    options.add_argument("--headless")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)

        time.sleep(3) # adjust if needed

        gp = driver.find_element(By.CSS_SELECTOR, "#ColInhalt > div > div:nth-child(2) > div > table > tbody > tr:nth-child(1) > td:nth-child(2)")
        ap = driver.find_element(By.CSS_SELECTOR, "#ColInhalt > div > div:nth-child(2) > div > table > tbody > tr:nth-child(1) > td:nth-child(3)")

        ap = transform_number(ap.text)
        gp = round((transform_number(gp.text)/12),2)  
        jp = round(gp * 12 + (ap / 100) * 2500, 2)

        return [("SW Bexbach Familie" , "66450", ap, gp, jp, "Strom")]
    
    except Exception as e:
        logging.exception(f"SW Bexbach scraper failed {e}")
    finally:
        driver.quit()
    return None

def get_sw_bexbach_gas():

    url = "https://www.stadtwerke-bexbach.de/de/Privatkunden/Erdgas/Preise-und-Tarife/"

    options = Options()
    options.add_argument("--headless")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(3)

        base_title = driver.find_element(By.CSS_SELECTOR, "#ColInhalt > div > div > table > tbody > tr:nth-child(1) > td:nth-child(1)")
        if base_title.text == "Grundpreis bis einschließlich 10 KW":
            gp_raw_base = driver.find_element(By.CSS_SELECTOR, "#ColInhalt > div > div > table > tbody > tr:nth-child(1) > td:nth-child(2)").text.strip()
            gp_base = round(transform_number(gp_raw_base), 2)
            ap_raw = driver.find_element(By.CSS_SELECTOR, "#ColInhalt > div > div > table > tbody > tr:nth-child(1) > td:nth-child(3)").text.strip()
            ap = transform_number(ap_raw)

        gp_title = driver.find_element(By.CSS_SELECTOR, "#ColInhalt > div > div > table > tbody > tr:nth-child(2) > td:nth-child(1)")
        if gp_title.text == "erhöht sich je weitere 5 KW um":
            gp_raw = driver.find_element(By.CSS_SELECTOR, "#ColInhalt > div > div > table > tbody > tr:nth-child(2) > td:nth-child(2)").text.strip()
            gp_add = transform_number(gp_raw) * 2
        gp = round((gp_base + gp_add) / 12, 2)
        jp = round(gp*12 + ap * 180, 2)
        
        return [("SW Bexbach Sondervertrag", "66450", ap, gp, jp, "Gas")]
    
    except Exception as e:
        logging.exception(f"SW Bexbach scraper failed {e}")
    finally:
        driver.quit()





def transform_number(response):
    match = re.search(r"[\d\.]+,\d+", response)
    if match:
        number_str = match.group()
        number_str = number_str.replace(".", "").replace(",", ".")
        return float(number_str)
    else:   
        logging.warning("Failed on regex")
        return None


if __name__ == "__main__":
    print(get_sw_bexback_data())
   # print(get_sw_bexbach_gas())
        