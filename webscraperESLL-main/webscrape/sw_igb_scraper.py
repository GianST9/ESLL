import requests
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_sw_igb_data():
    url = "https://www.sw-igb.de/stromtarife/?radio-persons=2500&tariff-consumption=2500&tariff-consumption-night=&tariff-zip=66386#tarife"
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        ap = extract_price(soup, 1)
        sp = extract_price(soup, 2)
        gp = extract_price(soup, 3)
        jp = extract_price(soup, 4)

        # Combine spot price and base price (monthly price)
        gp = round((sp + gp) / 12, 2)

        return [("SW IGB Privat", "66386", ap, gp, jp, "Strom")]
    
    except Exception as e:
        logging.exception(f"SW IGB scraper failed {e}")
        
        

def extract_price(soup, div_number):
    selector = f"body > div.content > div > main > div > div:nth-child(3) > div > div > div.tariff-wrapper__tariff.tariff-wrapper__tariff--highlight > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child({div_number}) > div.list-price-num"
    element = soup.select_one(selector)
    if not element:
        logging.exception(f"Price div number {div_number} not found on page!")
    return transform_number(element.text.strip())

def get_sw_igb_gas():

    url = "https://www.sw-igb.de/erdgas-tarife/?radio-persons=18000&tariff-consumption=18000#tarife"
    
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        pattern = re.compile(r'\bSondervereinbarung\w*\b.*\b31.12.2026\w*\b|\b31.12.2026\w*\b.*\bSondervereinbarung\w*\b', re.IGNORECASE)

        tariff_blocks = soup.select("body > div.content > div > main > div > div:nth-child(3) > div > div")

        for tariff_block in tariff_blocks:
            title_tag = tariff_block.select_one("div > div.tariff-wrapper__tariff__header > div.tariff-wrapper__tariff__header--title")
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                if pattern.search(title_text):
                    ap_raw = tariff_block.select_one("div > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(1) > div.list-price-num")
                    sp_raw = tariff_block.select_one("div > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(2) > div.list-price-num")
                    gp_raw = tariff_block.select_one("div > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(3) > div.list-price-num")
                    jp_raw = tariff_block.select_one("div > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(4) > div.list-price-num")
                    
                    if ap_raw and sp_raw and gp_raw and jp_raw:
                        ap = ap_raw.get_text(strip=True) 
                        ap = transform_number(ap)
                        
                        sp = sp_raw.get_text(strip=True)
                        sp = round(transform_number(sp), 2)

                        gp = gp_raw.get_text(strip=True) 
                        gp = round(transform_number(gp), 2)
                        
                        gp_res = round((sp + gp) / 12, 2)

                        jp = jp_raw.get_text(strip=True)
                        jp = transform_number(jp)

                        return [("SW St.Igb Sondervereinbarung LZ 26", "66386", ap, gp_res, jp, "Gas")]
                    
                    else:
                        logging.error("failed on html pattern")
                        return None
                    
    except Exception as e:
        logging.exception(f"SW IGB scraper failed {e}")


def transform_number(response):
    match = re.search(r"[\d\.]+,\d+", response)
    if match:
        number_str = match.group().replace(".", "").replace(",", ".")
        return float(number_str)
    else:   
        logging.error(f"Failed to parse number from: {response}")
        return None

if __name__ == "__main__":
    #print(get_sw_igb_data())
    print(get_sw_igb_gas())