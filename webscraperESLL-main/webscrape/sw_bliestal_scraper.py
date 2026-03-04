import logging
import requests
from bs4 import BeautifulSoup
import re
import certifi

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_sw_bliestal_data():

    url = "https://www.stadtwerke-bliestal.de/stromtarife/?radio-persons=2500&tariff-consumption=2500&tariff-consumption-night=&tariff-zip=66440#tarife"

    try: 
        response = requests.get(url, verify=certifi.where())
        response.raise_for_status()  
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # NOTE : Use selector: "body > div.content > div > main > div > div:nth-child(3) > div > div > div:nth-child(2) > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(1) > div.list-price-num" to get different tariff 
        
        arbeitspreis = soup.select("body > div.content > div > main > div > div:nth-child(3) > div > div > div:nth-child(1) > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(1) > div.list-price-num")[0].text.strip()
        sp = soup.select("body > div.content > div > main > div > div:nth-child(3) > div > div > div:nth-child(1) > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(2) > div.list-price-num")[0].text.strip()
        grundpreis = soup.select("body > div.content > div > main > div > div:nth-child(3) > div > div > div:nth-child(1) > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(3) > div.list-price-num")[0].text.strip()
        jahrpreis = soup.select("body > div.content > div > main > div > div:nth-child(3) > div > div > div:nth-child(1) > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(4) > div.list-price-num")[0].text.strip()
        
        ap = transform_number(arbeitspreis)
        sp = transform_number(sp)
        gp = transform_number(grundpreis)
        jp = transform_number(jahrpreis)

        gp = round((sp + gp) / 12, 2)

        return [("SW Bliestal Family", "66440", ap, gp, jp, "Strom")]
    
    except Exception as e:
        logging.exception(f"SW Bliestal scraper failed {e}")
    return None


def get_sw_bliestal_gas():
    url = "https://www.stadtwerke-bliestal.de/erdgas-tarife/?radio-persons=13000&tariff-consumption=18000#tarife"
    
    try:
        response = requests.get(url, verify=certifi.where())
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        pattern = re.compile(r'\bBLI\w*\b.*\b2026\w*\b|\b2026\w*\b.*\bBLI\w*\b', re.IGNORECASE)

        tariff_blocks = soup.select("body > div.content > div > main > div > div:nth-child(3) > div > div")

        for tariff_block in tariff_blocks:
            
            title_tag = tariff_block.select_one("div > div.tariff-wrapper__tariff__header > div.tariff-wrapper__tariff__header--title")
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                if pattern.search(title_text):

                    ap_raw = tariff_block.select_one("div > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(1) > div.list-price-num")
                    gp_raw = tariff_block.select_one("div > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(2) > div.list-price-num")
                    jp_raw = tariff_block.select_one("div > div.tariff-wrapper__tariff__price > div.list-prices > div:nth-child(3) > div.list-price-num")
                    if ap_raw and gp_raw and jp_raw:
                        ap = ap_raw.get_text(strip=True)
                        ap = transform_number(ap)

                        gp = gp_raw.get_text(strip=True)
                        gp = round(transform_number(gp)/ 12, 2)

                        jp = jp_raw.get_text(strip=True)
                        jp = transform_number(jp)

                        return [("SW Bliestal BLI LZ 26", "66440", ap, gp, jp, "Gas")]             
                    else:
                        logging.error("Failed on regex pattern")
                        return None
    except Exception as e:
        logging.exception(f"SW Bliestal scraper failed {e}")
    return None

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
    #print(get_sw_bliestal_data())
    print(get_sw_bliestal_gas())