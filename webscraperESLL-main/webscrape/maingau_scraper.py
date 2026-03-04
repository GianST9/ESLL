from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_maingau_gas():
    url = "https://www.maingau-energie.de/gas/tarifergebnis?sector=gas&consumption=18000&zip=66111&street=Rotenbergstr.&houseNumber=4&customer=private&cityId=11849&city=Saarbr%C3%BCcken&eco=false&kwkReference="

    options = Options()
    options.add_argument("--headless")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tariff_TariffColumn__4\\+BUi"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        pattern = re.compile(r"gas\s*komfort", re.IGNORECASE)
        result = []
        zip_code = "66111"

        tariff_boxes = soup.select("article[data-testid='energy-tariff']")

        for box in tariff_boxes:
            name_tag = box.select_one("h2.energy-tariffs-header_Headline__jW5Yz")
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)

            if pattern.search(name):
                try:

                    monthly_price_tag = box.select_one("p.energy-tariffs-header_Content__73IHT")
                    monthly_price = monthly_price_tag.get_text(strip=True).replace("mtl.", "").strip()

                    key_value_pairs = box.select("div.key-value-list_KeyPairRow__kaYRj")
                    grundpreis = arbeitspreis = None
                    for pair in key_value_pairs:
                        key = pair.select_one("dt").get_text(strip=True).lower()
                        value = pair.select_one("dd").get_text(strip=True)
                        if "grundpreis" in key:
                            grundpreis = value
                        elif "arbeitspreis" in key:
                            arbeitspreis = value

                    gp = round(transform_number(grundpreis) / 12, 2)
                    ap = transform_number(arbeitspreis)
                    jp = round(gp * 12 + ap * 180, 2)

                    return [(name, zip_code, ap, gp, jp, "Gas")]

                except Exception as e:
                    logging.error(f"Error parsing GasKomfort data: {e}")
                    continue

        return result
    except Exception as e:
        logging.exception(f"Maingau scraper failed {e}")
    finally:
        driver.quit()
    return None

def transform_number(response):
    match = re.search(r"[\d\.]+,\d+", response)
    if match:
        number_str = match.group().replace(".", "").replace(",", ".")
        return float(number_str)
    else:
        logging.warning(f"Failed to parse number from: {response}")
    return None 
    
if __name__ == "__main__":
    print(get_maingau_gas())