import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_eon_data():
    urls = [
        {
            "url": "https://occ.eon.de/productadvisor/5.0/offer/combined?city=Saarbr%C3%BCcken&clientId=eonde&consumption=2500&customerType=pc&persistToken=false&productName=E.ON+Klar+%C3%96koStrom+12&productType=power&tariffType=et&zipCode=66111&bonusType=NEW",
            "tariff_name": "E.ON Klar ÖkoStrom 12",
            "plz": "66111"
        },
        {
            "url": "https://occ.eon.de/productadvisor/5.0/offer/combined?city=Saarbr%C3%BCcken&clientId=eonde&consumption=2500&customerType=pc&persistToken=false&productName=E.ON+Klar+%C3%96koStrom+24&productType=power&tariffType=et&zipCode=66111&bonusType=NEW",
            "tariff_name": "E.ON Klar ÖkoStrom 24",
            "plz": "66111"
        },
        {
            "url": "https://occ.eon.de/productadvisor/5.0/offer/combined?city=Saarbr%C3%BCcken&clientId=eonde&consumption=2500&customerType=pc&persistToken=false&productName=E.ON+%C3%96koStrom+Solarpark&productType=power&tariffType=et&zipCode=66111&bonusType=NEW",
            "tariff_name": "E.ON ÖkoStrom Solarpark",
            "plz": "66111"
        }
    ]

    results = []

    for entry in urls:
        url = entry["url"]
        tariff_name = entry["tariff_name"]
        plz = entry["plz"]

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            price_details = data['product']['priceDetails']

            yearly_price = price_details.get('yearlyPrice', {}).get('default', {}).get('valueVat')
            base_price_month = price_details.get('basicPriceMonth', {}).get('valueVat')
            working_price = price_details.get('workingPrice', {}).get('singleTariff', {}).get('valueVat')
            bonus = float(price_details.get('bonus', {}).get('valueVat'))
  
            # Convert to float
            jp = round(float(yearly_price), 2)  # €/year
            gp = round(float(base_price_month), 2)  # €/month
            ap = round(float(working_price), 2)  # €/kWh ➜ ct/kWh

            results.append((tariff_name, plz, ap, gp, jp, "Strom", bonus))

        except requests.RequestException as e:
            logging.exception(f"Error fetching {url}: {e}")
        except KeyError as e:
            logging.exception(f"Key error: {e}")
        except (TypeError, ValueError) as e:
            logging.exception(f"Error parsing prices: {e}")

    return results

def get_eon_gas():
    
    api_url = "https://occ.eon.de/productadvisor/5.0/offer/combined?city=Saarbr%C3%BCcken&clientId=eonde&consumption=18000&customerType=pc&persistToken=false&productName=E.ON+Erdgas+24&productType=gas&tariffType=et&zipCode=66111&bonusType=NEW"
    
    try: 
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
#        with open ("response.json", "w") as json_file:
#            json.dump(data, json_file, indent=4)
        name = data['product']['name']
        if name == "E.ON Erdgas 24":
            price_details = data['product']['priceDetails']
            
            yearly_price = price_details.get('yearlyPrice', {}).get('default', {}).get('valueVat')
            base_price_month = price_details.get('basicPriceMonth', {}).get('valueVat')
            working_price = price_details.get('workingPrice', {}).get('singleTariff', {}).get('valueVat')
            bonus = price_details.get('bonus', {}).get('valueVat')
            
            
            
            jp = round(float(yearly_price), 2) 
            gp = round(float(base_price_month), 2)
            ap = round(float(working_price), 2)
            bonus = float(bonus)
            
            return [(name, "66111", ap, gp, jp, "Gas", bonus)]
        
    
    except requests.RequestException as e:
        logging.exception(f"Error fetching {api_url}: {e}")
    except KeyError as e:   
        logging.exception(f"Key error: {e}")
    except (TypeError, ValueError) as e:
        logging.exception(f"Error parsing prices: {e}")
    return None


if __name__ == "__main__":
    print(get_eon_data())
    #print(get_eon_gas())