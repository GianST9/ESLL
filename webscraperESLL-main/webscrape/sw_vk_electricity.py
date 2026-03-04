import time
import requests
import json
from sw_vk_bearer import get_bearer_token
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_sw_vk_data(token):
    """
    Retrieves electricity tariff information from the SW VK API using the provided bearer token.
    Parameters:
    token (str): The bearer token for authentication.
    Returns:
    A list containing the tariff name, postal code, annual price, monthly price, and yearly price.
    """
    
    api_url = "https://pricing-api.sls.epilot.io/v1/public/catalog/"

    if not token:
        logging.error("No token provided.")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
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

    payload = {
        "q": "(_id:1d018f70-d6de-4d26-88f5-8de3c35b316d AND active:true) OR (prices.$relation.entity_id:1d018f70-d6de-4d26-88f5-8de3c35b316d AND active:true) OR (_id:469d5515-b19c-4cfe-bcf8-18dba16dc973 AND active:true) OR (prices.$relation.entity_id:469d5515-b19c-4cfe-bcf8-18dba16dc973 AND active:true) OR (_id:4c3cbbec-db92-4e42-8609-49851fdb826b AND active:true) OR (prices.$relation.entity_id:4c3cbbec-db92-4e42-8609-49851fdb826b AND active:true) OR (_id:a70f9d75-2f2b-49df-ad1c-08720a9b744d AND active:true) OR (prices.$relation.entity_id:a70f9d75-2f2b-49df-ad1c-08720a9b744d AND active:true) OR (_id:6888d856-bdee-40f5-a2a9-769501bd8ee7 AND active:true) OR (prices.$relation.entity_id:6888d856-bdee-40f5-a2a9-769501bd8ee7 AND active:true) OR (_id:6846883f-a8ba-49f9-a93a-6b5cbb08c261 AND active:true) OR (prices.$relation.entity_id:6846883f-a8ba-49f9-a93a-6b5cbb08c261 AND active:true)",
        "hydrate": True
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            try:
                data = response.json()
                if len(data.get("results", [])) > 5:
                    gp = float(data["results"][5]["price_components"][0]["unit_amount_decimal"])
                    ap = float(data["results"][5]["price_components"][1]["unit_amount_decimal"])
                    ap = round(ap * 100, 2)
                    jp = (gp * 12 + ap/100 * 2500)

                    return [("SW VK my Strom Relax 2025", "66333", ap, gp, jp, "Strom")]
                else:
                    logging.exception("Data incomplete, retry needed.")
                    return None
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                logging.error("Error extracting unit_amount:", str(e))
                return None
        else:
            logging.error(f"POST failed: {response.status_code}")
            return None
    except Exception as e:
        logging.exception(f"SW VK Strom scraper failed {e}")
    return None

def runner():
    token = get_bearer_token()
    if not token:
        logging.error("Failed to get bearer token.")
        return
    
    while True:
        result = get_sw_vk_data(token)
        if result:
            return result
        else:
            logging.info("Log: SW VK data retrieval failed, retrying in 2min...")
            time.sleep(120)
            
if __name__ == "__main__":
    print(runner())