import requests
from sw_vk_bearer import get_bearer_token
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")



def get_sw_vk_gas(bearer_token):
    """
    Parameters:
    bearer_token (str): The bearer token for authentication.
    Returns:
    This function retrieves gas tariff information from the SW VK API using the provided bearer token.
    """
    
    api_url = "https://pricing-api.sls.epilot.io/v1/public/catalog"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "de,de-DE;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Origin": "https://journey.epilot.io",
        "Referer": "https://journey.epilot.io/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        "X-Ivy-Org-ID": "16582186",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "sec-ch-ua": "\"Microsoft Edge\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }

    payload = {"q":"(_id:f0a4523a-110a-41ff-b30b-b65fb0820a94 AND active:true) OR (prices.$relation.entity_id:f0a4523a-110a-41ff-b30b-b65fb0820a94 AND active:true) OR (_id:9166cd46-d517-4bef-a93b-a333b8f0acb8 AND active:true) OR (prices.$relation.entity_id:9166cd46-d517-4bef-a93b-a333b8f0acb8 AND active:true) OR (_id:9bf516b5-5c4d-439b-b5a5-394b1ed6229d AND active:true) OR (prices.$relation.entity_id:9bf516b5-5c4d-439b-b5a5-394b1ed6229d AND active:true) OR (_id:ecb89cd0-517b-40c8-bff6-ac08a62d5995 AND active:true) OR (prices.$relation.entity_id:ecb89cd0-517b-40c8-bff6-ac08a62d5995 AND active:true) OR (_id:6abad8cb-25f8-4127-9947-5e2f311bb20a AND active:true) OR (prices.$relation.entity_id:6abad8cb-25f8-4127-9947-5e2f311bb20a AND active:true) OR (_id:2528819b-d6bb-43c1-ae63-af95dbef25af AND active:true) OR (prices.$relation.entity_id:2528819b-d6bb-43c1-ae63-af95dbef25af AND active:true)","hydrate":True}
    
    try:
        
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        try:
            data = response.json()
            #with open ("response.json", "w") as json_file:
             #       json.dump(data, json_file, indent=4)
            if len(data.get("results", [])) > 5:
                gp = float(data["results"][4]["price_components"][0]["tiers"][2]["flat_fee_amount_decimal"])
                ap = float(data["results"][4]["price_components"][1]["tiers"][1]["unit_amount_decimal"])
                ap = round(ap * 100, 2)
                jp = (gp * 12 + ap/100 * 18000)
                return [("SW VK my Gas Relax 2025", "66333", ap, gp, jp, "Gas")]
                
            else:
                logging.exception("Data incomplete, retry needed")
                return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
                logging.error("Error extracting data")
                return None
    except Exception as e:
        logging.exception(f"SW VK Gas scraper failed {e}")
    return None
        

def runner():
    token = get_bearer_token()
    if not token:
        logging.error("No token provided.")
        return None     
    
    while True:
        result = get_sw_vk_gas(token)
        if result:
            return result
        else:
            logging.error("Log: SW VK Gas scraper failed...")
            return None
            
if __name__ == "__main__":
    print(runner())