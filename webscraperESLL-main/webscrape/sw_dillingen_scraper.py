import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)



def get_sw_dillingen_data():
    
    driver = create_driver()
    url = "https://kundenportal.swd-saar.de/powercommerce/csit3/fo/portal/start"
    try:
        
        driver.get(url)
        
        
        wait = WebDriverWait(driver, 10)
        
        field_privat_costumer = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#productSearchWidgetContent > div.panel-body > div:nth-child(1) > div > div:nth-child(1) > label > div")
        ))
        field_privat_costumer.click()
        
        field_electricity = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#productSearchWidgetContent > div.panel-body > div:nth-child(2) > div > div:nth-child(1) > label")
        ))
        field_electricity.click()
        
        field_consumption = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#productSearchConsumption")
        ))
        field_consumption.clear()
        field_consumption.send_keys("2500")	
        
        field_submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#productSearchButton")
        ))
        field_submit.click()
        
        result_container = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#tariffCollapse_2 > div > div.form-group.tariff-details > div.pricesAndConditions")
        ))
        
        if result_container:
            ap_response = driver.find_element(By.CSS_SELECTOR,
                "#tariffCollapse_2 > div > div.form-group.tariff-details > div.pricesAndConditions > div:nth-child(1) > div.pull-right.font-bold"
            )

            ap_raw = driver.execute_script("return arguments[0].textContent;", ap_response).strip()
            
            gp_response = driver.find_element(By.CSS_SELECTOR,
                "#tariffCollapse_2 > div > div.form-group.tariff-details > div.pricesAndConditions > div:nth-child(2) > div.pull-right.font-bold"
            )
            gp_raw = driver.execute_script("return arguments[0].textContent;", gp_response).strip()
            
            ap = transform_number(ap_raw)
            gp = round(transform_number(gp_raw) /12, 2)
            jp = gp * 12 + ap / 100 * 2500
            
            return [("SW Dillingen Solarstrom", "66763", ap, gp, jp, "Strom")]
    
    except Exception as e:      
        logging.exception(f"SW Dillingen scraper failed {e}")
    finally:
        driver.quit()
        
def get_sw_dillingen_gas():
    
    driver = create_driver()
    url = "https://kundenportal.swd-saar.de/powercommerce/csit3/fo/portal/start"
    try:
        
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        
        field_privat_costumer = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#productSearchWidgetContent > div.panel-body > div:nth-child(1) > div > div:nth-child(1) > label > div")
        ))
        field_privat_costumer.click()
        
        field_gas = wait.until(EC.element_to_be_clickable(  ### FAILES at selecting gas field
            (By.CSS_SELECTOR, "#mediaType_GAS")
        ))    
        field_gas.click()
        
        field_consumption = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#consumptionInput")
        ))
        field_consumption.clear()
        field_consumption.send_keys("18000")
        
        field_submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#button_productSearchv3_data_search")
        ))
        field_submit.click()
        
        result_container = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#tariffCollapse_2 > div > div.form-group.tariff-details > div.pricesAndConditions")
        ))
        
        if result_container:
            ap_response = driver.find_element(By.CSS_SELECTOR,
                "#tariffCollapse_1 > div > div.form-group.tariff-details > div.pricesAndConditions > div:nth-child(1) > div.pull-right.font-bold")
            ap_raw = driver.execute_script("return arguments[0].textContent;", ap_response).strip()
            gp_response = driver.find_element(By.CSS_SELECTOR,
                "#tariffCollapse_1 > div > div.form-group.tariff-details > div.pricesAndConditions > div:nth-child(2) > div.pull-right.font-bold"
            )
            gp_raw = driver.execute_script("return arguments[0].textContent;", gp_response).strip()
            ap = transform_number(ap_raw)
            gp = round(transform_number(gp_raw) /12, 2)
            jp = gp * 12 + ap / 100 * 18000
            return [("SW Dillingen Erdgas", "66763", ap, gp, jp, "Gas")]            
        
    finally:
        driver.quit()
    
      
def transform_number(response):
    match = re.search(r"[\d\.]+,\d+", response)
    if match:
        number_str = match.group()
        number_str = number_str.replace(".", "").replace(",", ".")
        return float(number_str)
    else:   
        print("Failed on regex")
        return None
      
        
if __name__ == "__main__":
    print(get_sw_dillingen_data())
    #print(get_sw_dillingen_gas())
    #NOTE script is not working for gas 