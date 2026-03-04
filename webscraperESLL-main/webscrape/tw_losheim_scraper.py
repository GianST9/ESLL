import requests
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_tw_losheim_data():
    """
    Returns 1 list. 
    Searching by html selector
    """
    
    try:
        url = "https://www.twl-losheim.de/energie/strom"

        response = requests.get(url)
        response.raise_for_status() 

        soup = BeautifulSoup(response.text, 'html.parser')

        content = soup.select("#c85 > div >div > p:nth-child(3) > strong")[0].get_text()

        numbers = re.findall(r"[\d,.]+", content)

        grundpreis = float(numbers[0].replace(',', '.'))
        gp = round(grundpreis/12, 2)
        ap = float(numbers[1].replace(',', '.'))
        jp = round(gp * 12 + (ap / 100) * 2500, 2)

        return [("TW Losheim", "66679", ap, gp, jp, "Strom")]

    except Exception as e:
        logging.exception("TW Losheim Strom scraper failed")
        return []



def get_tw_losheim_gas():
    """
    Returns 1 list. 
    Searching by html selector
    """
    
    try:
        url = "https://www.twl-losheim.de/energie/erdgas/erdgaspreise"

        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.select_one("#c4097 > div > table > tbody > tr:nth-child(3) > td:nth-child(1)").text.strip()
        if title == "Heizgasvollversorgung":
            gp = soup.select_one("#c4097 > div > table > tbody > tr:nth-child(3) > td:nth-child(3)").text.strip()
            ap = soup.select_one("#c4097 > div > table > tbody > tr:nth-child(3) > td:nth-child(5)").text.strip()

            gp = transform_number(gp)
            ap = transform_number(ap)
            jp = gp * 12 + 180 * ap

            return [("TW Losheim GV", "66679", ap, gp, jp, "Gas")]
        
    except Exception as e:
        logging.exception("TW Losheim gas scraper failed")
        return []
        


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
    #print(get_tw_losheim_data())
    print(get_tw_losheim_gas())
