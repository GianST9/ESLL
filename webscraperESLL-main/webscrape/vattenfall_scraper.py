import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import quote
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_vattenfall_data():
    """
    Returns the first 2 Tariffs of the Webpage, searching by html selector
    """
    
    
    url = "https://www.vattenfall.de/angebote/guenstiger-strom?postalCode=66111&consumption=2500&city=Saarbr%C3%BCcken&streetName=&streetHouseNumber=&district=&energyTypeSelected=electricity"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(5)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        product_lists = soup.select('div.productSlim')
        results = []

        for idx, product in enumerate(product_lists, start=1):
            
            title_el = product.select_one('div.productSlim__tariff__headline h3')
            #print(title_el)
            title_text = title_el.get_text(strip=True) if title_el else "Name not found"

            table_rows = product.select('table tr')
            ap = gp = 0.0
            for row in table_rows:
                cells = row.select('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if "Verbrauchspreis" in key:
                        ap = transform_number(value)
                    elif "Grundpreis" in key:
                        gp = transform_number(value)

                    bonus_spans = product.select('div.productSlim__benefits span.text--bold')
                    bonus1 = bonus2 = 0.0
                    if len(bonus_spans) >= 1:
                        try:
                            bonus1 = transform_number(bonus_spans[0].get_text(strip=True))
                        except ValueError:
                            bonus1 = 0.0
                    if len(bonus_spans) >= 2:
                        try:
                            bonus2 = transform_number(bonus_spans[1].get_text(strip=True))
                        except ValueError:
                            bonus2 = 0.0

                    total_bonus = bonus1 + bonus2


            jp = gp * 12 + ap / 100 * 2500 

            results.append((f"Vattenfall {title_text}", "66111", ap, gp, jp, "Strom", total_bonus))

            if idx == 2:
                break

        driver.quit()
        return results if results else None

    except Exception as e:
        logging.exception(f"Vattenfall scraper failed {e}")
    return None


def get_vattenfall_gas():
    """
    Returns the first 2 Tariffs of the Webpage, searching by html selector
    """
    
    url = "https://www.vattenfall.de/angebote/guenstiges-gas?postalCode=66111&consumption=18000&city=Saarbr%C3%BCcken&streetName=&streetHouseNumber=&district=&energyTypeSelected=gas"

    options = Options()
    options.add_argument("--headless") 
    service = Service()  
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        time.sleep(5)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        
        product_lists = soup.select('#products > div > div > div > div')

        results = []
        for idx, product in enumerate(product_lists, start=1):
            
            try:
                title = product.select_one('h3').get_text(strip=True)

                ap = product.select_one('table > tbody > tr:nth-child(3) > td.text--right > p')
                gp = product.select_one('table > tbody > tr:nth-child(4) > td.text--right > p')
                if ap and gp:
                    ap = transform_number(ap.get_text(strip=True))
                    gp = transform_number(gp.get_text(strip=True))              
                    jp = round(gp * 12 + ap / 1 * 180, 2)
                    
                    bonus_spans = product.select('div.productSlim__benefits span.text--bold')
                    bonus1 = bonus2 = 0.0
                    if len(bonus_spans) >= 1:
                        try:
                            bonus1 = transform_number(bonus_spans[0].get_text(strip=True))
                        except ValueError:
                            bonus1 = 0.0
                    if len(bonus_spans) >= 2:
                        try:
                            bonus2 = transform_number(bonus_spans[1].get_text(strip=True))
                        except ValueError:
                            bonus2 = 0.0

                    total_bonus = bonus1 + bonus2
                    
                    results.append((f"Vattenfall {title}", "66111", ap, gp, jp, "Gas", total_bonus))
                    
                if idx == 2:
                    break
            except Exception as e:
                logging.error(f"Error processing product {idx}: {e}")
                continue

        return results if results else None
    
    except Exception as e:
        logging.exception(f"Vattenfall scraper failed {e}")
    finally:
            driver.quit()
    return None

def transform_number(text):
    """
    Extract a German‑formatted number from *text*.
    Accepts
      • '1.234,56 €'
      • '234,5 ct/kWh'
      • '150 €'
      • '140'
    """
    m = re.search(r"[\d.]+(?:,\d+)?", text)
    if not m:
        logging.error(f"Failed to parse number from: {text!r}")

    num_str = m.group().replace(".", "").replace(",", ".")
    return float(num_str)
    
    
if __name__ == "__main__":
    print(get_vattenfall_data())
    #print(get_vattenfall_gas())