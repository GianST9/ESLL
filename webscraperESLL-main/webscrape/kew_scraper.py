from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_kew_cookie():
    options = Options()
    options.add_argument("--headless")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    try: 
        driver.get("https://www.kew.de/strom/strom-fuer-haushalte/")
        selenium_cookies = driver.get_cookies()
    except:
        logging.warning("Failed retrieving cookie")
    finally:
        driver.quit()

    cookie_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    cookie_string = "; ".join([f"{name}={value}" for name, value in cookie_dict.items()])
    return cookie_string

def transform_number(response):
    if isinstance(response, (int, float)):
        return float(response)
    response = str(response).replace('\xa0', ' ').replace('€', '').replace('Cent', '').strip()
    response = response.replace(".", "").replace(",", ".")
    try:
        return float(response)
    except ValueError:
        logging.exception(f"Failed to convert: {response}")
        return None

def get_kew_data(cookie_string, plz="66538", consumption_kwh=2500, target_tariff_id="S-129F27a", list_tariffs=False):
    api_url = "https://kew.de/api/cors"
    headers = {
        "Accept": "*/*",
        "Content-Type": "text/plain;charset=UTF-8",
        "Cookie": cookie_string,
        "Origin": "https://www.kew.de",
        "Referer": "https://www.kew.de/",
        "User-Agent": "Mozilla/5.0",
    }
    payload = {
        "customerType": "PRIVATE",
        "mediaTypeRaw": "POWER",
        "mediaType": "POWER",
        "pointOfConsumption": {
            "postalCode": int(plz),
            "city": "Neunkirchen"
        },
        "consumptions": {
            "DEFAULT_TARIFF": str(consumption_kwh)
        }
    }

    response = requests.post(api_url, json=payload, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses

    try:
        data = response.json()
        tariffs_list = data.get("tariffs", [])

        if not tariffs_list:
            print("No 'tariffs' found in response")
            return None
        
#        with open ("response.json", "w") as json_file:
#            json.dump(data, json_file, indent=4)
        #if list_tariffs:
        #    print("\nAvailable tariffs:")
        #    for tariff in tariffs_list:
        #        print(f"ID: {tariff.get('TariffID')} - Name: {tariff.get('TariffName')}")
        #    print("\n")  
        
        target_tariff = None
        for tariff in tariffs_list:
            if tariff.get("TariffID") == target_tariff_id:
                target_tariff = tariff
                break

        if not target_tariff:
            logging.warning(f"Target tariff ID '{target_tariff_id}' not found!")
            return None

        grundpreis = None
        arbeitspreis = None

        for part in target_tariff.get("TariffParts", []):
            if part.get("Type") == "GP":
                slices = part.get("TimeSlices", [])[0].get("ConsumptionSlices", [])
                if slices:
                    grundpreis = slices[0].get("Price", {}).get("Brutto")
            elif part.get("Type") == "AP":
                slices = part.get("TimeSlices", [])[0].get("ConsumptionSlices", [])
                if slices:
                    arbeitspreis = slices[0].get("Price", {}).get("Brutto")

        result = [(target_tariff.get("TariffName", "N/A"), plz, transform_number(arbeitspreis), transform_number(grundpreis), transform_number(target_tariff.get("PriceYear")), "Strom")]
        return result

    except json.JSONDecodeError:
        logging.error("Failed to parse JSON")
        return None
    

def get_kew_gas(cookie_string):

    api_url = "https://kew.de/api/cors"
    headers = {
        "Accept": "*/*",
        "Content-Type": "text/plain;charset=UTF-8",
        "Cookie": cookie_string,
        "Origin": "https://www.kew.de",
        "Referer": "https://www.kew.de/",
        "User-Agent": "Mozilla/5.0",
    }
    payload = {
        "customerType": "PRIVATE",
        "mediaTypeRaw": "GAS",
        "mediaType": "GAS",
        "pointOfConsumption": {
            "postalCode": int(66538),
            "city": "Neunkirchen"
        },
        "consumptions": {
            "DEFAULT_TARIFF": str(18000)
        }
    }

    try: 
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        jp = data["tariffs"][0]["PriceYear"]
        ap = round(data["tariffs"][0]["TariffParts"][0]["TimeSlices"][0]["ConsumptionSlices"][0]["Price"]["Brutto"], 2)
        gp = data["tariffs"][0]["TariffParts"][1]["TimeSlices"][0]["ConsumptionSlices"][0]["Price"]["Brutto"]
        return [("KEW Komfort Gas", "66538", ap, gp, jp, "Gas")]
    
    except:
        logging.error("Failed to parse JSON")
        return None
        


if __name__ == "__main__":
    cookie_string = get_kew_cookie()

    #print(get_kew_gas(cookie_string))
    #get_kew_data(cookie_string, list_tariffs=True)
    print(get_kew_data(cookie_string, target_tariff_id="S-129F27a"))