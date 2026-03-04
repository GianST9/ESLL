#import sqlite3 old database
from dotenv import load_dotenv
import pyodbc
from datetime import datetime
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import scrapers
from eprimo_scraper import get_cookie as get_eprimo_cookie, get_eprimo_data, get_eprimo_gas
from sw_igb_scraper import get_sw_igb_data, get_sw_igb_gas
from sw_sulzbach_srcaper import get_sw_sulzbach_data, get_sw_sulzbach_gas
from sw_merzig_scraper import get_sw_merzig_data, get_sw_merzig_gas
from sw_saarlouis_scraper import get_sw_saarlouis_data, get_sw_saarlouis_gas
from kommpower_scraper import get_kommpower_data, get_kommpower_gas
from eon_scraper import get_eon_data, get_eon_gas
from vattenfall_scraper import get_vattenfall_data, get_vattenfall_gas
from energis_scraper import get_energis_data, get_cookie, get_energis_gas
from kew_scraper import get_kew_cookie, get_kew_data, get_kew_gas
from sw_stwendel_scraper import get_sw_stwendel_data, get_sw_stwendel_gas
from sw_kirkel_scraper import get_sw_kirkel_data, get_sw_kirker_gas
from sw_bliestal_scraper import get_sw_bliestal_data, get_sw_bliestal_gas
from sw_bexbach_scraper import get_sw_bexback_data, get_sw_bexbach_gas
from tw_losheim_scraper import get_tw_losheim_data, get_tw_losheim_gas
from enbw_scraper import get_enbw_data
from sw_dillingen_scraper import get_sw_dillingen_data #, get_sw_dillingen_gas
from sw_vk_electricity import runner as vk_elec_runner
from sw_vk_gas import runner as gas_runner
from maingau_scraper import get_maingau_gas

import logging
from logging.handlers import RotatingFileHandler
import os


@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_delay: float = 60.0  # 1 minute
    backoff_factor: float = 2.0
    max_delay: float = 600.0  # 10 minutes
    
RETRY_CONFIG = RetryConfig()

os.makedirs("logs", exist_ok=True)
log_handler = RotatingFileHandler("logs/scraper_pipeline.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',  datefmt='%Y-%m-%d %H:%M:%S')
log_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(log_handler)
logger.addHandler(console_handler)

logging.basicConfig(level=logging.INFO, handlers=[log_handler, console_handler]) 
# Suppress loggers
logging.getLogger("seleniumwire").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


#load_dotenv()  
def get_db_connection():
    #server = os.getenv('DB_SERVER')
    #database = 'Marktpreise'
    #username = os.getenv('DB_USER')
    #password = os.getenv('DB_PASSWORD')
    #port = os.getenv('DB_PORT', '1433')
    server='scn-sql-prd'
    port='1433'
    database = 'Marktpreise'
    username='saleski'
    password='saleski'

    conn_str = (
        f'DRIVER={{SQL Server}};'
        f'SERVER={server},{port};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        'TrustServerCertificate=yes;'
    )

    return pyodbc.connect(conn_str)

# SQL - DB-Schema -> in MSSQL
def create_tariffs_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        IF NOT EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'tariffs'
        )
        BEGIN
            CREATE TABLE tariffs (
                id INT IDENTITY(1,1) PRIMARY KEY,
                company_name NVARCHAR(255) NOT NULL,
                tariff_name NVARCHAR(255) NOT NULL,
                type NVARCHAR(50) NOT NULL,
                timestamp DATE,
                plz NVARCHAR(10),
                ap FLOAT,
                gp FLOAT,
                jp FLOAT,
                bonus FLOAT NULL,
                CONSTRAINT unique_tariff UNIQUE(company_name, tariff_name, type, timestamp, plz)
            )
        END
    ''')
    conn.commit()
    cursor.close()

def create_scraper_failures_table(conn):
    """Create table to track scraper failures and retry attempts"""
    cursor = conn.cursor()
    cursor.execute('''
        IF NOT EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'scraper_failures'
        )
        BEGIN
            CREATE TABLE scraper_failures (
                id INT IDENTITY(1,1) PRIMARY KEY,
                company_name NVARCHAR(255) NOT NULL,
                power_type NVARCHAR(50) NOT NULL,
                failure_timestamp DATETIME NOT NULL,
                error_message NVARCHAR(MAX),
                retry_count INT DEFAULT 0,
                resolved BIT DEFAULT 0,
                resolved_timestamp DATETIME NULL
            )
        END
    ''')
    conn.commit()
    cursor.close()

def log_scraper_failure(conn, company_name: str, power_type: str, error_message: str, retry_count: int = 0):
    """Log a scraper failure to the database"""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scraper_failures (company_name, power_type, failure_timestamp, error_message, retry_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (company_name, power_type, datetime.now(), str(error_message), retry_count))
        conn.commit()
        cursor.close()
    except Exception as e:
        logging.error(f"Failed to log scraper failure: {e}")

def mark_scraper_resolved(conn, company_name: str, power_type: str):
    """Mark a scraper failure as resolved"""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE scraper_failures 
            SET resolved = 1, resolved_timestamp = ?
            WHERE company_name = ? AND power_type = ? AND resolved = 0
        ''', (datetime.now(), company_name, power_type))
        conn.commit()
        cursor.close()
    except Exception as e:
        logging.error(f"Failed to mark scraper as resolved: {e}")
    

def insert_tariff(conn, company_name, tariff_name, tariff_type, plz, ap, gp, jp, bonus=None):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tariffs (company_name, tariff_name, type, plz, timestamp, ap, gp, jp, bonus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (company_name, tariff_name, tariff_type, plz, datetime.now().date().isoformat(), float(ap), float(gp), float(jp), bonus))
        conn.commit()
        cursor.close()
        logging.info(f"Inserted: {company_name} - {tariff_name}")
    except pyodbc.IntegrityError:
        logging.warning(f"Already exists today: {company_name} - {tariff_name}. Skipping.")
    except Exception as e: 
        logging.error(f"Insert error for {company_name} - {tariff_name}: {e}")


def scraper_data_exists_today(conn, company_name, power_type):
    """
    check if data for the company & powertype already exists for today
    if it does, skip the scraper
    """
    today = datetime.now().date().isoformat()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM tariffs 
        WHERE company_name = ? AND timestamp = ? AND type = ?
    ''', (company_name, today, power_type))
    result = cursor.fetchone()
    cursor.close()
    return result is not None

def validate_tariff_data(tariffs: List) -> bool:
    """Validate that tariff data is not empty and contains valid data"""
    if not tariffs or len(tariffs) == 0:
        return False
    
    # Additional validation - check if tariffs contain valid data
    for tariff in tariffs:
        if not tariff or len(tariff) < 6:  # Minimum expected fields
            return False
        
        # Check if essential fields are not None/empty
        tariff_name, plz, ap, gp, jp = tariff[0], tariff[1], tariff[2], tariff[3], tariff[4]
        if not all([tariff_name, plz is not None, ap is not None, gp is not None, jp is not None]):
            return False
    
    return True

# Strom runner function

def run_eprimo_elec():
    cookie = get_eprimo_cookie()
    return get_eprimo_data(cookie)

def run_sw_igb_elec():
    return get_sw_igb_data()

def run_sw_sulzbach_elec():
    return get_sw_sulzbach_data()

def run_sw_merzig_elec():
    return get_sw_merzig_data()

def run_sw_saarlouis_elec():
    return get_sw_saarlouis_data()

def run_sw_vk_elec():
    return vk_elec_runner()

def run_kommpower_elec():
    return get_kommpower_data()

def run_eon_elec():
    return get_eon_data()

def run_vattenfall_elec():
    return get_vattenfall_data()

def run_energis_elec():
    cookie_string = get_cookie()
    plz_list = ["66111", "66701"]  # SB, Beckingen
    return get_energis_data(cookie_string, plz_list)

def run_kew_elec():
    cookie_string = get_kew_cookie()  
    return get_kew_data(cookie_string)

def run_sw_stwendel_elec():
    return get_sw_stwendel_data()

def run_sw_kirkel_elec():
    return get_sw_kirkel_data()

def run_sw_bliestal_elec():
    return get_sw_bliestal_data()

def run_sw_bexbach_elec():
    return get_sw_bexback_data()

def run_tw_losheim_elec():
    return get_tw_losheim_data()

def run_enbw_elec():
    return get_enbw_data()

def run_dillingen_elec():
    return get_sw_dillingen_data()


# Gas runner functions
def run_eprimo_gas():
    cookie = get_eprimo_cookie()
    return get_eprimo_gas(cookie)

def run_sw_igb_gas():
    return get_sw_igb_gas()

def run_sw_sulzbach_gas():
    return get_sw_sulzbach_gas()

def run_sw_merzig_gas():
    return get_sw_merzig_gas()

def run_sw_saarlouis_gas():
    return get_sw_saarlouis_gas()

def run_kommpower_gas():
    return get_kommpower_gas()

def run_eon_gas():
    return get_eon_gas()

def run_vattenfall_gas():
    return get_vattenfall_gas()

def run_energis_gas():
    cookie_string = get_cookie()
    plz_list = ["66111", "66701"]
    return get_energis_gas(cookie_string, plz_list)

def run_kew_gas():
    cookie_string = get_kew_cookie()
    return get_kew_gas(cookie_string)

def run_sw_stwendel_gas():
    return get_sw_stwendel_gas()

def run_sw_kirkel_gas():
    return get_sw_kirker_gas()

def run_sw_bliestal_gas():
    return get_sw_bliestal_gas()

def run_sw_bexbach_gas():
    return get_sw_bexbach_gas()

def run_tw_losheim_gas():
    return get_tw_losheim_gas()

#def run_dillingen_gas():
#    return get_sw_dillingen_gas()

def run_sw_vk_gas():
    return gas_runner()

def run_maingau_gas():
    return get_maingau_gas()

# List of scrapers to run
SCRAPERS = [
    # Strom scraper 
    {
        "company_name": "eprimo",
        "power_type": "Strom",
        "runner": run_eprimo_elec
    },
    {
        "company_name": "SW IGB",
        "power_type": "Strom",
        "runner": run_sw_igb_elec
    },
    {
        "company_name": "SW Sulzbach",
        "power_type": "Strom",
        "runner": run_sw_sulzbach_elec
    },
    {
        "company_name": "SW Merzig",
        "power_type": "Strom",
        "runner": run_sw_merzig_elec
    },
    {
        "company_name": "SW Saarlouis",
        "power_type": "Strom",
        "runner": run_sw_saarlouis_elec
    },
    {
        "company_name": "SW Völklingen",
        "power_type": "Strom",
        "runner": run_sw_vk_elec
    },
    {
        "company_name": "Kommpower",
        "power_type": "Strom",
        "runner": run_kommpower_elec
    },
    {
        "company_name": "E.ON",
        "power_type": "Strom",
        "runner": run_eon_elec
    },
    {
        "company_name": "Vattenfall",
        "power_type": "Strom",
        "runner": run_vattenfall_elec
    },
    {
        "company_name": "Energis",
        "power_type": "Strom",
        "runner": run_energis_elec
    },
    {
        "company_name": "Kew",
        "power_type": "Strom",
        "runner": run_kew_elec
    },
    {
        "company_name": "SW St. Wendel",
        "power_type": "Strom",
        "runner": run_sw_stwendel_elec
    },
    {
        "company_name": "SW Kirkel",
        "power_type": "Strom",
        "runner": run_sw_kirkel_elec
    },
    {
        "company_name": "SW Bliestal",
        "power_type": "Strom",
        "runner": run_sw_bliestal_elec
    },
    {
        "company_name": "SW Bexbach",
        "power_type": "Strom",
        "runner": run_sw_bexbach_elec
    },
    {
        "company_name": "TW Losheim",
        "power_type": "Strom",
        "runner": run_tw_losheim_elec
    },
    {
        "company_name": "EnBW",
        "power_type": "Strom",
        "runner": run_enbw_elec
    },
    {
        "company_name": "SW Dillingen",
        "power_type": "Strom",
        "runner": run_dillingen_elec
    },
    # Gas scrapers
    {
        "company_name": "eprimo",
        "power_type": "Gas",
        "runner": run_eprimo_gas
    },
    {
        "company_name": "SW IGB",
        "power_type": "Gas",
        "runner": run_sw_igb_gas
    },
    {
        "company_name": "SW Sulzbach",
        "power_type": "Gas",
        "runner": run_sw_sulzbach_gas
    },
    {
        "company_name": "SW Merzig",
        "power_type": "Gas",
        "runner": run_sw_merzig_gas
    },
    {
        "company_name": "SW Saarlouis",
        "power_type": "Gas",
        "runner": run_sw_saarlouis_gas
    },
    {
        "company_name": "SW Völklingen",
        "power_type": "Gas",
        "runner": run_sw_vk_gas
    },
    {
        "company_name": "Kommpower",
        "power_type": "Gas",
        "runner": run_kommpower_gas
    },
    {
        "company_name": "E.ON",
        "power_type": "Gas",
        "runner": run_eon_gas
    },
    {
        "company_name": "Vattenfall",
        "power_type": "Gas",
        "runner": run_vattenfall_gas
    },
    {
        "company_name": "Energis",
        "power_type": "Gas",
        "runner": run_energis_gas
    },
    {
        "company_name": "Kew",
        "power_type": "Gas",
        "runner": run_kew_gas
    },
    {
        "company_name": "SW St. Wendel",
        "power_type": "Gas",
        "runner": run_sw_stwendel_gas
    },
    {
        "company_name": "SW Kirkel",
        "power_type": "Gas",
        "runner": run_sw_kirkel_gas
    },
    {
        "company_name": "SW Bliestal",
        "power_type": "Gas",
        "runner": run_sw_bliestal_gas
    },
    {
        "company_name": "SW Bexbach",
        "power_type": "Gas",
        "runner": run_sw_bexbach_gas
    },
    {
        "company_name": "TW Losheim",
        "power_type": "Gas",
        "runner": run_tw_losheim_gas
    },
#    {
#        "company_name": "SW Dillingen",
#        "power_type": "Gas",
#        "runner": run_dillingen_gas
#    },
    {
        "company_name": "Maingau",
        "power_type": "Gas",
        "runner": run_maingau_gas
    },
]


async def run_scraper_with_retry(scraper: Dict[str, Any], conn, retry_count: int = 0) -> bool:
    """
    Run a scraper with retry logic using exponential backoff.
    Returns True if successful, False if all retries failed.
    """
    company_name = scraper["company_name"]
    power_type = scraper["power_type"]
    runner = scraper["runner"]

    try:
        logging.info(f"Starting scraper for {company_name} ({power_type}) - Attempt {retry_count + 1}")
        
        # Run blocking scraper code in a thread
        tariffs = await asyncio.to_thread(runner)
        logging.info(f"Returned {len(tariffs) if tariffs else 0} tariffs from {company_name} ({power_type})")
        
        # Validate the returned data
        if not validate_tariff_data(tariffs):
            raise ValueError(f"Invalid or empty tariff data returned from {company_name} ({power_type})")
        
        # Insert tariffs into database
        inserted_count = 0
        for tariff in tariffs:
            try:
                if len(tariff) == 7:
                    tariff_name, plz, ap, gp, jp, tariff_type, bonus = tariff
                else:
                    tariff_name, plz, ap, gp, jp, tariff_type = tariff
                    bonus = None  
                insert_tariff(conn, company_name, tariff_name, tariff_type, plz, ap, gp, jp, bonus)
                inserted_count += 1
            except Exception as insert_error:
                logging.error(f"Error inserting tariff from {company_name}({power_type}): {insert_error}")
        
        if inserted_count == 0:
            raise ValueError(f"No tariffs were successfully inserted for {company_name} ({power_type})")
        
        logging.info(f"Successfully finished scraper for {company_name} ({power_type}) - Inserted {inserted_count} tariffs")
        
        # Mark as resolved if this was a retry
        if retry_count > 0:
            mark_scraper_resolved(conn, company_name, power_type)
        
        return True
        
    except Exception as e:
        error_msg = f"Exception in scraper {company_name} ({power_type}) - Attempt {retry_count + 1}: {str(e)}"
        logging.error(error_msg)
        
        # Log failure to database
        log_scraper_failure(conn, company_name, power_type, str(e), retry_count)
        
        # Check if we should retry
        if retry_count < RETRY_CONFIG.max_retries:
            # Calculate delay with exponential backoff
            delay = min(
                RETRY_CONFIG.initial_delay * (RETRY_CONFIG.backoff_factor ** retry_count),
                RETRY_CONFIG.max_delay
            )
            
            logging.info(f"Will retry {company_name} ({power_type}) in {delay:.1f} seconds...")
            await asyncio.sleep(delay)
            
            # Recursive retry
            return await run_scraper_with_retry(scraper, conn, retry_count + 1)
        else:
            logging.error(f"Maximum retries exceeded for {company_name} ({power_type}). Giving up.")
            return False


async def run_scraper(scraper, conn):
    """
    Run a scraper and insert the results into the database.
    """
    company_name = scraper["company_name"]
    power_type = scraper["power_type"]

    if scraper_data_exists_today(conn, company_name, power_type):
        logging.info(f"Data for {company_name} already exists for {power_type} today. Skipping scraper.")
        return True

    return await run_scraper_with_retry(scraper, conn)
    
    
sem = asyncio.Semaphore(3)  # adjust to avoid overloading threads

async def run_scraper_with_semaphore(scraper, conn) -> bool:
    async with sem:
        return await run_scraper(scraper, conn)

async def run_pipeline_async():
    conn = get_db_connection()
    print("Connected to SQL Server successfully!")
    create_tariffs_table(conn)
    create_scraper_failures_table(conn)

    # Run all scrapers with semaphore control
    tasks = [run_scraper_with_semaphore(scraper, conn) for scraper in SCRAPERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Analyze results
    successful_scrapers = 0
    failed_scrapers = 0
    
    for i, result in enumerate(results):
        scraper = SCRAPERS[i]
        company_name = scraper["company_name"]
        power_type = scraper["power_type"]
        
        if isinstance(result, Exception):
            logging.error(f"Scraper {company_name} ({power_type}) failed with exception: {result}")
            failed_scrapers += 1
        elif result is True:
            successful_scrapers += 1
        else:
            logging.warning(f"Scraper {company_name} ({power_type}) completed but returned unexpected result: {result}")
            failed_scrapers += 1
    
    # Log final summary
    total_scrapers = len(SCRAPERS)
    logging.info(f"Pipeline completed: {successful_scrapers}/{total_scrapers} scrapers successful, {failed_scrapers} failed")
    
    if failed_scrapers > 0:
        logging.warning(f"WARNING: {failed_scrapers} scrapers failed after all retry attempts. Check logs for details.")
    else:
        logging.info("SUCCESS: All scrapers completed successfully!")

    conn.close()

# Optional: Function to run only failed scrapers from previous runs
async def retry_failed_scrapers():
    """Run only scrapers that failed in previous runs and haven't been resolved"""
    conn = get_db_connection()
    
    # Get unresolved failures from today
    cursor = conn.cursor()
    today = datetime.now().date()
    cursor.execute('''
        SELECT DISTINCT company_name, power_type 
        FROM scraper_failures 
        WHERE CAST(failure_timestamp AS DATE) = ? AND resolved = 0
    ''', (today,))
    
    failed_scrapers_data = cursor.fetchall()
    cursor.close()
    
    if not failed_scrapers_data:
        logging.info("No failed scrapers to retry.")
        conn.close()
        return
    
    # Find corresponding scrapers to retry
    scrapers_to_retry = []
    for company_name, power_type in failed_scrapers_data:
        for scraper in SCRAPERS:
            if scraper["company_name"] == company_name and scraper["power_type"] == power_type:
                scrapers_to_retry.append(scraper)
                break
    
    logging.info(f"Retrying {len(scrapers_to_retry)} failed scrapers...")
    
    # Run retry tasks
    tasks = [run_scraper_with_semaphore(scraper, conn) for scraper in scrapers_to_retry]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log retry results
    successful_retries = sum(1 for result in results if result is True)
    logging.info(f"Retry completed: {successful_retries}/{len(scrapers_to_retry)} scrapers now successful")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--retry-failed":
        asyncio.run(retry_failed_scrapers())
    else:
        asyncio.run(run_pipeline_async())
    
    sys.exit(0)
    
    
    #python -m PyInstaller --onefile  --name data_pipeline --add-data ".env;." --add-data "C:\\Users\\STEFANIAGianluca(Ene\\AppData\\Roaming\\Python\\Python312\\site-packages\\seleniumwire\\ca.crt;seleniumwire"  --add-data "C:\\Users\\STEFANIAGianluca(Ene\\AppData\\Roaming\\Python\\Python312\\site-packages\\seleniumwire\\ca.key;seleniumwire"  data_pipeline.py