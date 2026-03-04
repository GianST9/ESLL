import requests
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


import requests
from bs4 import BeautifulSoup
import logging


def get_sw_kirkel_data():
    url = "https://www.gwkirkel.de/strom/tarifuebersicht/gwk-stromrelax-2026"
    try:
        response = requests.get(url)
        response.raise_for_status() 

        soup = BeautifulSoup(response.text, 'html.parser')


        arbeitspreis = soup.select(
            "#\\38 fad567e-7f85-411d-b7bc-ff28d6eeef75 > div:nth-child(2) > div > div:nth-child(3) > div > ul > li:nth-child(1) > p"
        )[0].text.strip()

        grundpreis = soup.select(
            "#\\38 fad567e-7f85-411d-b7bc-ff28d6eeef75 > div:nth-child(2) > div > div:nth-child(3) > div > ul > li:nth-child(2) > p"
        )[0].text.strip()

        ap = transform_number(arbeitspreis)
        gp = transform_number(grundpreis)
        jp = round(gp * 12 + (ap / 100) * 2500, 2)

        return [("SW Kirkel Relax 2026", "66459", ap, gp, jp, "Strom")]
    
    except Exception as e:
        logging.exception(f"SW Kirkel scraper failed: {e}")


def get_sw_kirker_gas():
    url = "https://www.gwkirkel.de/gas/tarifuebersicht/gwk-komfort-gas"
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        ap = soup.select("#\\35 605b4f9-3531-49ad-ad7c-7eb6442f6ac9 > div:nth-child(2) > div > div:nth-child(3) > div > ul > li:nth-child(1) > p")[0].text.strip()
        ap = transform_number(ap)

        gp = soup.select("#\\35 605b4f9-3531-49ad-ad7c-7eb6442f6ac9 > div:nth-child(2) > div > div:nth-child(3) > div > ul > li:nth-child(2) > p")[0].text.strip()

        gp = transform_number(gp)

        jp = round(gp * 12 + (ap/100) * 18000, 2)
        ap = round(ap, 2)

        return [("SW Kirkel Komfort Gas", "66459",ap, gp, jp, "Gas")]
    
    except Exception as e:
        logging.exception(f"SW Kirkel scraper failed {e}")


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
    #print(get_sw_kirkel_data())
    print(get_sw_kirker_gas())