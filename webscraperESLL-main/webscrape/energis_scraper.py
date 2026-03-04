from datetime import datetime
import json
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_cookie():
    url = "https://energis.de"

    options = Options()
    options.add_argument("--headless")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        time.sleep(2)
        selenium_cookies = driver.get_cookies()
    except Exception as e:
        logging.exception("Failed retrieving cookies")
        return ""
    finally:
        driver.quit()

    cookie_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    cookie_string = "; ".join([f"{name}={value}" for name, value in cookie_dict.items()])
    return cookie_string


def extract_product_info(product, plz, tariff_name):
    price = product.get("product_price", {})
    haupttarif = price.get("haupttarif", {})
    bonus = price.get("grundpreis", {})

    try:
        jp = round(float(price.get("consumption_price_total_gross", 0)), 2)
    except (ValueError, TypeError):
        jp = 0.0

    try:
        gp = round(float(price.get("base_price_total_gross", 0)) / 12, 2)
    except (ValueError, TypeError):
        gp = 0.0

    try:
        ap_raw = str(haupttarif.get("price_value_gross", "0"))[:4]
        ap = round(float(ap_raw) / 100, 2)
    except (ValueError, TypeError):
        ap = 0.0
    try:
        if (str(bonus.get("bonus_status"))):        
            bonus = float(bonus.get("bonus_value"))
        else:
            bonus = 0.0
    except (ValueError, TypeError):
        bonus = 0.0
        
    return (tariff_name, plz, ap, gp, jp, "Strom", float(bonus))


def find_products(obj, plz):
    products = []
    if isinstance(obj, dict):
        if "product_price" in obj:
            products.append(obj)
        for v in obj.values():
            products.extend(find_products(v, plz))
    elif isinstance(obj, list):
        for item in obj:
            products.extend(find_products(item, plz))
    return products


def get_energis_data(cookie_string, plz_list=["66111", "66701"]):
    

    api_url = "https://energis.de/api/order-line/search/energy"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Cookie": cookie_string,
    }

    all_results = []
    
    delivery_start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for plz in plz_list:
        payload = {
            "section": "strom",
            "consumption_ht": "2500",
            "consumption_nt": "0",
            "consumption_type": "Haushalt",
            "customer_journey": "ijoin",
            "delivery_start_date": f"{delivery_start_date}",
            "consumption_address": {"zipcode": plz}
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

#            with open ("response.json", "w") as json_file:
#                json.dump(data, json_file, indent=4)

            products = find_products(data, plz)[:2]  # Only first 2 products
            if len(products) >= 2:
                all_results.append(extract_product_info(products[0], plz, "energis Strom Online"))
                all_results.append(extract_product_info(products[1], plz, "energis Strom komfort"))
            else:
                logging.warning("Not enough products found")

        except requests.RequestException as e:
            logging.error(f"Request error for PLZ {plz}: {e}")
        except ValueError as e:
            logging.error(f"Error parsing JSON for PLZ {plz}: {e}")

    return all_results


def get_energis_gas(cookie_string, plz_list = ["66111", "66701"]):

    api_url = "https://energis.de/api/order-line/search/energy"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Cookie": cookie_string,
    }

    all_results = []
    
    delivery_start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for plz in plz_list:
        payload = {
            "section": "gas",
            "consumption_ht": "18000",
            "consumption_nt": "0",
            "consumption_type": "Haushalt",
            "customer_journey": "ijoin",
            "delivery_start_date": f"{delivery_start_date}",
            "consumption_address": {"zipcode": plz}
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
#            with open ("response.json", "w") as json_file:
#                json.dump(data, json_file, indent=4)

            jp = data["data"]["tariffs"][1]["product_price"]["consumption_price_total_gross"]
            gp = data["data"]["tariffs"][1]["product_price"]["base_price_total_gross"]
            ap = data["data"]["tariffs"][1]["product_price"]["haupttarif"]["price_value_gross"]
            bonus = data["data"]["tariffs"][1]["product_price"]["grundpreis"]["bonus_value"]
            gp = round(gp /12, 2)
            ap = str(ap)[:4]
            ap = round(float(ap) / 100, 2)
            
            all_results.append(("energis Gas Komfort", f"{plz}", ap, gp, jp, "Gas", float(bonus))) 

        
        except requests.RequestException as e:
            logging.error(f"Request error for PLZ {plz}: {e}")
        except ValueError as e:
            logging.error(f"Error parsing JSON for PLZ {plz}: {e}")
        except KeyError as e:
            logging.error(f"Missing expected Key in response for {plz}: {e}")

    return all_results




if __name__ == "__main__":
    cookie_string = get_cookie()
    #print(get_energis_data(cookie_string, ["66111", "66701"]))

    print(get_energis_gas(cookie_string, ["66111", "66701"]))
   