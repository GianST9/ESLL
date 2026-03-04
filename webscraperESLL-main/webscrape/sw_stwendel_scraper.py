import re
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def transform_number(response):
    if isinstance(response, (int, float)):
        return float(response)
    response = str(response).replace('\xa0', ' ').replace('€', '').replace('Cent', '').strip()
    response = response.replace(".", "").replace(",", ".")
    try:
        return float(response)
    except ValueError:
        logging.exception(f"Failed to convert: {response}")
        return None

def get_sw_stwendel_data(url="https://stadtwerke-st-wendel.de/strom/strom-tarifuebersicht/", debug=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; scraper/1.0; +https://example.org/bot)"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # 1) Best / robust approach: search the page text for the SSW Strom 2 block
        page_text = soup.get_text(separator="\n")
        # compact multiple blank lines
        page_text = re.sub(r"\n\s*\n+", "\n\n", page_text)

        # Capture the SSW Strom 2 section between the heading and the next tariff or section title
        block_regex = re.compile(
            r"SSW\s+Strom\s+2(.*?)(?:SSW\s+Strom\s+3|Kombinierbar|##\s+SSW\s+Strom|$)",
            re.IGNORECASE | re.DOTALL,
        )
        mblock = block_regex.search(page_text)

        gp = ap = None

        if mblock:
            block = mblock.group(1)
            if debug:
                logging.info("Found SSW Strom 2 text block.")
                logging.debug("\n" + block)

            # Try direct capture like "Grundpreis: 16,50 EUR/Monat"
            gp_m = re.search(r"Grundpreis:\s*([\d\.\,]+)", block, re.IGNORECASE)
            ap_m = re.search(r"Arbeitspreis:\s*([\d\.\,]+)", block, re.IGNORECASE)

            if gp_m:
                try:
                    gp = transform_number(gp_m.group(1))
                except Exception:
                    gp = None
            if ap_m:
                try:
                    ap = transform_number(ap_m.group(1))
                except Exception:
                    ap = None

        # 2) Fallback: scan whole page for "Grundpreis" and "Arbeitspreis" occurrences and pair with nearest tariff header
        if (gp is None) or (ap is None):
            if debug:
                logging.info("Falling back to scanning all 'Grundpreis' / 'Arbeitspreis' occurrences.")
            lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
            for idx, ln in enumerate(lines):
                if re.search(r"SSW\s+Strom\s+2", ln, re.IGNORECASE):
                    # look forward a few lines for Grundpreis / Arbeitspreis
                    window = "\n".join(lines[idx: idx + 8])
                    gp_m = re.search(r"Grundpreis:\s*([\d\.\,]+)", window, re.IGNORECASE)
                    ap_m = re.search(r"Arbeitspreis:\s*([\d\.\,]+)", window, re.IGNORECASE)
                    if gp_m and (gp is None):
                        gp = transform_number(gp_m.group(1))
                    if ap_m and (ap is None):
                        ap = transform_number(ap_m.group(1))
                    if (gp is not None) and (ap is not None):
                        break

        if debug:
            logging.info(f"Parsed values -> Grundpreis (gp): {gp} ; Arbeitspreis (ap): {ap}")

        if gp is None or ap is None:
            logging.error("Could not extract gp and/or ap from page.")
            # Optionally dump some nearby content to help debugging
            if debug:
                # print first 800 chars of the page text to debug
                logging.debug(page_text[:800])
            return None

        # Calculation: gp is EUR/month, ap is ct/kWh -> convert ap/100 to EUR/kWh
        yearly_price = round(gp * 12 + (ap / 100.0) * 2500, 2)

        # Return same format as your previous function
        return [("SW St. Wendel SSW Strom 2", "66606", ap, gp, yearly_price, "Strom")]

    except Exception as e:
        logging.exception(f"SW StWendel scraper failed: {e}")
        return None

        

def get_sw_stwendel_gas(url="https://stadtwerke-st-wendel.de/erdgas-und-waerme/erdgas-und-waerme-tarifuebersicht/", debug=False):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; scraper/1.0; +https://example.org/bot)"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Get the plain text of the whole page
        page_text = soup.get_text(separator="\n")
        page_text = re.sub(r"\n\s*\n+", "\n\n", page_text)

        # Capture the SSW Gas 2 section
        block_regex = re.compile(
            r"SSW\s+Gas\s+2(.*?)(?:SSW\s+Gas\s+3|Kombinierbar|$)",
            re.IGNORECASE | re.DOTALL,
        )
        mblock = block_regex.search(page_text)

        gp = ap = None

        if mblock:
            block = mblock.group(1)
            if debug:
                logging.info("Found SSW Gas 2 text block.")
                logging.debug("\n" + block)

            gp_m = re.search(r"Grundpreis:\s*([\d\.\,]+)", block, re.IGNORECASE)
            ap_m = re.search(r"Arbeitspreis:\s*([\d\.\,]+)", block, re.IGNORECASE)

            if gp_m:
                try:
                    gp = transform_number(gp_m.group(1))
                except Exception:
                    gp = None
            if ap_m:
                try:
                    ap = transform_number(ap_m.group(1))
                except Exception:
                    ap = None

        # Fallback: scan for Gas 2 heading and following lines
        if gp is None or ap is None:
            if debug:
                logging.info("Falling back to scanning all 'Grundpreis'/'Arbeitspreis' occurrences for Gas 2.")
            lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
            for idx, ln in enumerate(lines):
                if re.search(r"SSW\s+Gas\s+2", ln, re.IGNORECASE):
                    window = "\n".join(lines[idx: idx + 8])
                    gp_m = re.search(r"Grundpreis:\s*([\d\.\,]+)", window, re.IGNORECASE)
                    ap_m = re.search(r"Arbeitspreis:\s*([\d\.\,]+)", window, re.IGNORECASE)
                    if gp_m and gp is None:
                        gp = transform_number(gp_m.group(1))
                    if ap_m and ap is None:
                        ap = transform_number(ap_m.group(1))
                    if gp is not None and ap is not None:
                        break

        if debug:
            logging.info(f"Parsed values -> Grundpreis (gp): {gp} ; Arbeitspreis (ap): {ap}")

        if gp is None or ap is None:
            logging.error("Could not extract gp/ap for Gas 2")
            if debug:
                logging.debug(page_text[:800])
            return None

        # Gas calc: gp EUR/month, ap ct/kWh, consumption 18,000 kWh
        yearly_price = round(gp * 12 + (ap / 100.0) * 18000, 2)

        return [("SW St. Wendel SSW Gas 2", "66606", ap, gp, yearly_price, "Gas")]

    except Exception as e:
        logging.exception(f"SW StWendel gas scraper failed: {e}")
        return None


if __name__ == "__main__":
    print(get_sw_stwendel_data())
    print(get_sw_stwendel_gas())