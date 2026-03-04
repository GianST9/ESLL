import re
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_sw_merzig_data():
    try:
        url = "https://bestellung.stadtwerke-merzig.de/tarifergebnis/?formBlockID=25155&tariff_type_iframe=1&customer_type_iframe=0&heating_type=pump&zip_tariff_calculator=66663&city_iframe=Merzig&street_iframe=Am+Sportplatz&consumption_iframe=2500&consumption_ht=&consumption_nt=&submit_tariff_form=&counter_type_1=1&customer_type_tariffcalc=0&tariff_type_mirror=1&skip_inputs=heating_type%2Cconsumption_ht%2Cconsumption_nt%2Ccounter_type_1"
        response = requests.get(url)
        response.raise_for_status()  

        soup = BeautifulSoup(response.text, 'html.parser')
        #NOTE : Use GB/AP/JP [0] to get Komfortstrom, [1] to get Landstrom
        grundpreis = soup.select("#block-id-3473 > div > p > span.font-weight-bold")
        gp = transform_number(grundpreis[1].text.strip())

        arbeitspreis = soup.select("#block-id-3480 > div > p > span.font-weight-bold")
        ap = transform_number(arbeitspreis[1].text.strip())

        jahrespreis = soup.select("#block-id-4171 > div > p > span.font-weight-bold")
        jp = transform_number(jahrespreis[1].text.strip())

        return [("SW Merzig Landstrom", "66663", ap, gp , jp, "Strom")]
    
    except Exception as e:
        logging.exception(f"SW Merzig scraper failed {e}")
    return None
    


def get_sw_merzig_gas():

    url = "https://bestellung.stadtwerke-merzig.de/tarifergebnis/?formBlockID=25155&tariff_type_iframe=0&customer_type_iframe=0&heating_type=pump&zip_tariff_calculator=66663&city_iframe=Merzig&street_iframe=Abteistr.&consumption_iframe=18000&consumption_ht=&consumption_nt=&submit_tariff_form=&counter_type_1=1&customer_type_tariffcalc=0&tariff_type_mirror=0&skip_inputs=heating_type%2Cconsumption_ht%2Cconsumption_nt%2Ccounter_type_1"
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        #NOTE: use [1] for different tariff
        grundpreis = soup.select("#block-id-3473 > div > p > span.font-weight-bold")
        gp = transform_number(grundpreis[0].text.strip())

        arbeitspreis = soup.select("#block-id-3480 > div > p > span.font-weight-bold")
        ap = transform_number(arbeitspreis[0].text.strip())

        jahrespreis = soup.select("#block-id-4171 > div > p > span.font-weight-bold")
        jp= transform_number(jahrespreis[0].text.strip())

        return [("SW Merzig Komfortgas", "66663", ap, gp, jp, "Gas")]
    
    except Exception as e:
        logging.exception(f"SW Merzig scraper failed {e}")
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
    #get_sw_merzig_data()
    print(get_sw_merzig_gas())
    


