import re
from bs4 import BeautifulSoup
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")



def get_kommpower_data(target_product_id="Haushalt1_GWH"):
    api_url = "https://gw.production.wlp.cloud/kom/api/v2/products/prices"

    product_codes = [
        "Haushalt2_GWH",
        "Kommpower_Mobil_Plus_GWH",
        "Haushalt1_GWK",
        "Kommpower_Mobil_Plus_GWK",
        "Haushalt1_SWL",
        "Kommpower_Mobil_Plus_SWL",
        "Haushalt1_GWH"
    ]

    params = {
        "zip_code": "66265",
        "usage": "2500",
        "energy_type": "electricity",
        "campaign": "WLPCLOUD",
        "product_codes": json.dumps(product_codes)  # must be JSON string
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://kommpower.de",
        "Referer": "https://kommpower.de/"
    }

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        with open ("response.json", "w") as json_file:
            json.dump(data, json_file, indent=4)
            
        # Map product codes -> product names
        available_products = {
            product.get("product_code"): product.get("product_name")
            for product in data.get("products", [])
        }

        if target_product_id not in available_products:
            logging.error(f"Target product '{target_product_id}' not found!")
            return []

        target_product = next(
            (p for p in data["products"] if p.get("product_code") == target_product_id),
            None
        )

        if not target_product or "prices" not in target_product:
            logging.error("Prices not found in target product")
            return []

        prices = target_product["prices"]

        try:
            gp = round(float(prices.get("monthly_base_price_brutto", 0)), 2)
            ap = round(float(prices.get("working_price_brutto", 0)), 4)
            jp = round(float(prices.get("total_base_price_brutto", 0)), 2)
        except (TypeError, ValueError):
            logging.error("Error parsing product prices")
            return []

        return [("Kommpower Haushalt", "66265", ap, gp, jp, "Strom")]

    except requests.RequestException as e:
        logging.error(f"Failed to fetch Kommpower data: {e}")
    except (ValueError, KeyError) as e:
        logging.error(f"Failed to parse Kommpower JSON: {e}")





def get_kommpower_gas():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=chrome_options)

    try:
        url = "https://kommpower.de/gas/"
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "tablepress-3"))
        )

        gp_elements = driver.find_elements(By.CSS_SELECTOR, "#tablepress-3 > tbody > tr.row-2.even > td.column-3")
        ap_elements = driver.find_elements(By.CSS_SELECTOR, "#tablepress-3 > tbody > tr.row-3.odd > td.column-3")


        gp_texts = [el.text for el in gp_elements]
        ap_texts = [el.text for el in ap_elements]

        gp_list = [transform_number(text) for text in gp_texts if transform_number(text) is not None]
        ap_list = [transform_number(text) for text in ap_texts if transform_number(text) is not None]

        if not gp_list or not ap_list:
            raise ValueError("GP or AP list is empty. Check Cloudflare, selectors or page structure.")

        gp_value = gp_list[0]
        ap_value = ap_list[0]

        jp = round(18000 * (ap_value / 100) + gp_value, 2) 
        gp_monthly = round(gp_value / 12 , 2)

        return [("Kommpower Gas", "66265",ap_value, gp_monthly, jp, "Gas")]
    
    except ValueError as e:
        logging.error(f"Failed in kommpower: {e}")
    except:
        logging.error(f"Failed in kommpower")
    
    finally:
        driver.quit()



def transform_number(response):
    match = re.search(r"[\d\.]+,\d+", response)
    if match:
        number_str = match.group()
        number_str = number_str.replace(".", "").replace(",", ".")
        return float(number_str)
    else:   
        logging.warning("Failed on regex", response)
        return None
    

    
if __name__ == "__main__":

    #print(get_kommpower_gas())
    print(get_kommpower_data())