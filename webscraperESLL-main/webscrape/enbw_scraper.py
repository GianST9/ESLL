from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
from urllib.parse import quote
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def transform_number(response):
    match = re.search(r"[\d\.]+,\d+", response)
    if match:
        number_str = match.group()
        number_str = number_str.replace(".", "").replace(",", ".")
        return float(number_str)
    else:   
        logging.warning("Failed on regex", response)
        return None
    

def get_enbw_data():
    plz = 66111
    consumption = 2450

    url = f"https://www.enbw.com/strom/ausgezeichneter-stromanbieter?Postleitzahl={plz}&Verbrauch={consumption}&Typ=Strom&context=shared.offercontext.electricity.no-dst.pk#tarife"

    options = Options()
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)

        time.sleep(5)  # adjust for website's API response time

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        product_containers = soup.find_all('div', attrs={"data-product-slug": True})

        for i, product in enumerate(product_containers, 1):
            slug = product['data-product-slug']


            price_bonus_container = product.find("div", class_="product-info-price-bonus__container")
            
            if price_bonus_container:
                bonus_element = price_bonus_container.find("div", class_="product-info-price-bonus__bonus")
                if bonus_element:
                    bonus = bonus_element.text.strip().replace('€', '').strip()
                    
                else:
                    logging.warning("enbw Bonus not found")      
                
            else:
                    print("enbw Bonus not found")  
                    
            # Contract Details
            gp = ap = "Not found"
            contract_data = product.find_next("div", attrs={"data-cy": "product-info-contract-data"})
            if contract_data:
                values = contract_data.find_all("span", class_="product-contract-data__value")
                if len(values) >= 2:
                    gp = values[0].text.strip()
                    ap = values[1].text.strip()


            first_year_prices = contract_data.find_next("div", class_="product-price-first-year")
            if first_year_prices:
                first_year_values = first_year_prices.find_all("span", class_="product-contract-data__value")
                if len(first_year_values) >= 3:
                    jp = first_year_values[0].text.strip()


            if i == 1:
                ap = transform_number(ap)
                gp = transform_number(gp)
                jp = transform_number(jp)

                return [(slug, "66111", ap, gp, jp, "Strom", float(bonus))] #add Bonus; float(bonus)
        
        logging.warning("No valid product in EnBW")
    
    except Exception as e:
        logging.exception(f"EnBW Scraper failed {e}")
        return []

    finally:
        driver.quit()
    

if __name__ == "__main__":
    print(get_enbw_data())