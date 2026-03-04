import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_cookie():
    
    url = "https://www.eprimo.de/?hp=8000000451&utm_source=google&utm_medium=cpc&utm_campaign=eprimo_brand_exact_2862-1&utm_content=140448510470&utm_term=2862-1_eprimo__e&gclsrc=aw.ds&gad_source=1&gclid=Cj0KCQjw2tHABhCiARIsANZzDWpav_LdKBPD9M7v42tC1jKcwXiMC6Dpvw6i4ZoVNys4ygpgIHuh29IaAnshEALw_wcB#gad_source_1"

    options = Options()
    options.add_argument("--headless") 
    service = Service()  
    driver = webdriver.Chrome(service=service, options=options)
    try: 
        driver.get(url)
        selenium_cookies = driver.get_cookies()
    except:
        logging.exception("Failed retrieving cookies")
    finally:
        driver.quit()

    cookie_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    cookie_string = "; ".join([f"{name}={value}" for name, value in cookie_dict.items()])
    
    return cookie_string


def get_eprimo_data(cookie_string):
    
    api_url = "https://api.eprimo.de/api/v1/page/?path=%2Ftarifrechner-angebote%3Fplz%3D66111%26sparte%3D10%26kwh%3D2500%26aktion%3D12411013%26pricesDisplayDefault%3Dm"
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": cookie_string,
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        json_data = response.json()
            
            
        sorted_tariffs = json_data["pageContent"]["customData"]["tariffCalculatorResults.page.tariffs"]["sortedTariffs"]

        if len(sorted_tariffs) >= 3:
            tariff3 = sorted_tariffs[2] # change here for different tariff

            ap = float(tariff3.get("workingRate1"))    
            gp = float(tariff3.get("basePriceMonth"))

            jahrespreis = gp * 12 + (ap / 100) * 2500
            jahrespreis = round(jahrespreis, 2)
            
            return [("eprimoStrom PrimaKlima Pur", "66111", ap, gp, jahrespreis, "Strom")]
        
        else:
            logging.warning("Less than 3 tariffs available in sortedTariffs")
    except Exception as e:
        logging.error(f"eprimo scraper failed {e}")
    return None


def get_eprimo_gas(cookie_string):
    api_url = "https://api.eprimo.de/api/v1/page/?path=%2Ftarifrechner-angebote%3Fplz%3D66111%26sparte%3D20%26kwh%3D18000%26aktion%3D12411013%26pricesDisplayDefault%3Dm"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": cookie_string,
    }
    try: 
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        data = response.json()

        tariff = data["pageContent"]["customData"]["tariffCalculatorResults.page.tariffs"]["sortedTariffs"][0]
        ap = float(tariff.get("workingRate1"))
        gp = float(tariff.get("basePriceMonth"))
        jp = 12 * gp + 180 * ap 

        return [("Eprimo PrimaKlima pur", "66111", ap, gp , jp, "Gas")] 
    
    except Exception as e:
        logging.error(f"eprime scraper failed {e}")
    return None

if __name__ == "__main__":
    cookie_string = get_cookie()
    print(get_eprimo_data(cookie_string))
    #print(get_eprimo_gas(cookie_string))
