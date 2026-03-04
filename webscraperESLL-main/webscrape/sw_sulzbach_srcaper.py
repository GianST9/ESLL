from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")



def get_tariff_url(path, type):
    base_url = "https://www.stadtwerke-sulzbach.de"
    url = urljoin(base_url, path)
    
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # regex pattern for : "einfach", "linear"
        if type == "Strom":
            pattern = re.compile(r'\beinfach\w*\b.*\blinear\w*\b|\blinear\w*\b.*\beinfach\w*\b', re.IGNORECASE)
        elif type == "Gas":
            pattern = re.compile(r'\bXXL\w*\b.*\bHeizgas\w*\b|\bHeizgas\w*\b.*\bXXL\w*\b', re.IGNORECASE)

        tariff_blocks = soup.select('div.tariffs div.maxwidth div > a')

        for link_tag in tariff_blocks:
            title_tag = link_tag.select_one('div > div.title')
            if title_tag:
                text = title_tag.get_text(strip=True)
                if pattern.search(text):
                    target_url = urljoin(base_url, link_tag.get('href'))
                    return target_url
    except Exception as e:
        logging.exception(f"Failed to find URL")
    return None

def get_sw_sulzbach_gas():

    tariff_name = "SW Sulzbach XXL Heizgas"
    path = "/product/2"
    type = "Gas"
    url = get_tariff_url(path, type)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses

        return html_filter(tariff_name, response, type)
    except Exception as e:
        logging.exception(f"SW Sulzbach scraper failed {e}")
    return None
                          
                          
def get_sw_sulzbach_data():

    tariff_name = 'SW Sulzbach einfach linear'
    path = "/product/1"
    type = "Strom"
    url = get_tariff_url(path, type)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses

        return html_filter(tariff_name, response, type)
    except Exception as e:
        logging.exception(f"SW Sulzbach scraper failed {e}")
    return None

def html_filter(tariff_name ,response, type):


    soup = BeautifulSoup(response.text, 'html.parser')


    content = soup.select_one("body > div.product_page > div:nth-child(2) > div.width_2_3 ")
    if content:
        text = content.get_text(separator=' ', strip=True)

        numbers = re.findall(r'\d+,\d+', text)

        float_values = [float(num.replace(',', '.')) for num in numbers]
        ap = round(float_values[0],2)
        if type == "Strom":
            gp = round((float_values[1] /12) ,2)
            jp = round(gp * 12 + (ap / 100) * 2500, 2)
        else:
            gp = round((float_values[1]), 2)
            jp = round(gp * 12 + (ap / 100) * 18000, 2)

        return [(tariff_name, "66290", ap, gp , jp, type)]
        
    else:
        logging.error("HTML filter error")
        return None


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
    print(get_sw_sulzbach_data())
    print(get_sw_sulzbach_gas())
    #print(get_tariff_url())
    