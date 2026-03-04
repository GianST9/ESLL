# Energy Tariff Scraper Pipeline

##  Description

This Python application is an automated web scraping pipeline that collects electricity and gas tariff data from energy providers. The system uses asynchronous processing with retry logic and exponential backoff to ensure reliable data collection. All scraped data is stored in a SQL Server database with automatic deduplication and logging.

The pipeline includes error handling, failure tracking, and the ability to retry failed scrapers. It's designed to run daily and automatically skips companies that have already been scraped for the current day.

##  Scraped Companies

###  Electricity (Strom) Providers
- **eprimo**
- **SW IGB** (Stadtwerke IGB)
- **SW Sulzbach** (Stadtwerke Sulzbach)
- **SW Merzig** (Stadtwerke Merzig)
- **SW Saarlouis** (Stadtwerke Saarlouis)
- **SW Völklingen** (Stadtwerke Völklingen)
- **Kommpower**
- **E.ON**
- **Vattenfall**
- **Energis**
- **Kew**
- **SW St. Wendel** (Stadtwerke St. Wendel)
- **SW Kirkel** (Stadtwerke Kirkel)
- **SW Bliestal** (Stadtwerke Bliestal)
- **SW Bexbach** (Stadtwerke Bexbach)
- **TW Losheim** (Technische Werke Losheim)
- **EnBW** (Energie Baden-Württemberg)
- **SW Dillingen** (Stadtwerke Dillingen)

###  Gas Providers
- **eprimo**
- **SW IGB** (Stadtwerke IGB)
- **SW Sulzbach** (Stadtwerke Sulzbach)
- **SW Merzig** (Stadtwerke Merzig)
- **SW Saarlouis** (Stadtwerke Saarlouis)
- **SW Völklingen** (Stadtwerke Völklingen)
- **Kommpower**
- **E.ON**
- **Vattenfall**
- **Energis**
- **Kew**
- **SW St. Wendel** (Stadtwerke St. Wendel)
- **SW Kirkel** (Stadtwerke Kirkel)
- **SW Bliestal** (Stadtwerke Bliestal)
- **SW Bexbach** (Stadtwerke Bexbach)
- **TW Losheim** (Technische Werke Losheim)
- **Maingau**

##  Requirements

Create a `requirements.txt` file with the following dependencies:

```txt
beautifulsoup4==4.13.4
blinker==1.6.2
bs4==0.0.2
certifi==2025.4.26
numpy==2.2.5
pandas==2.2.3
pyodbc==5.2.0
selenium==4.32.0
selenium-wire==5.1.0
SQLAlchemy==2.0.41
urllib3==2.4.0
webdriver-manager==4.0.2
websocket-client==1.8.0
```
Also either Chrome or its binaries are needed to run the program

##  Installation

1. **Install Python 3.12 or higher**
2. **Clone the repository:**
   ```bash
   git clone https://github.com/GianST9/ESLL.git
   cd energy-tariff-scraper
   ```
3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Ensure you have access to the SQL Server database specified in the connection string**

##  Usage

### Run Full Pipeline
```bash
python data_pipeline.py
```

### Retry Only Failed Scrapers
```bash
python data_pipeline.py --retry-failed
```

## 🔨 Building Executable

The application can be built into an executable using PyInstaller:

```bash
python -m PyInstaller --onefile \
  --add-data "[PATH_TO_PYTHON_PACKAGES]/seleniumwire/ca.crt;seleniumwire" \
  --add-data "[PATH_TO_PYTHON_PACKAGES]/seleniumwire/ca.key;seleniumwire" \
  data_pipeline.py
```

> **⚠️ Note:** Replace `[PATH_TO_PYTHON_PACKAGES]` with your actual Python packages path.
>
> **Example paths:**
> - **Windows:** `C:\Users\[USERNAME]\AppData\Roaming\Python\Python312\site-packages`
> - **Linux/Mac:** `~/.local/lib/python3.12/site-packages`
>
> The `--add-data` parameters are necessary to include SSL certificates required by selenium-wire.

##  Features

-  **Asynchronous Processing**: Runs multiple scrapers concurrently with semaphore control
-  **Retry Logic**: Automatic retry with exponential backoff for failed scrapers
-  **Data Validation**: Validates scraped data before database insertion
-  **Duplicate Prevention**: Automatically skips companies already scraped today
-  **Comprehensive Logging**: Detailed logs with rotation support
-  **Failure Tracking**: Database tracking of scraper failures and resolutions
-  **Error Handling**: Robust error handling for network and parsing issues

## 🗄 Database Schema

The application creates two main tables:

### `tariffs` Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INT (Primary Key) | Auto-incrementing ID |
| `company_name` | NVARCHAR(255) | Energy provider name |
| `tariff_name` | NVARCHAR(255) | Name of the tariff |
| `type` | NVARCHAR(50) | 'Strom' or 'Gas' |
| `timestamp` | DATE | Date of data collection |
| `plz` | NVARCHAR(10) | Postal code |
| `ap` | FLOAT | Arbeitspreis (working price) |
| `gp` | FLOAT | Grundpreis (basic price) |
| `jp` | FLOAT | Jahrespreis (annual price) |
| `bonus` | FLOAT | Optional bonus amount |

### `scraper_failures` Table
- Tracks failed scraper attempts and retry counts
- Enables targeted retry of only failed scrapers
- Includes failure timestamps and error messages

## ⚙ Configuration

Key configuration options can be found in the `RetryConfig` dataclass:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_retries` | 3 | Maximum retry attempts |
| `initial_delay` | 60.0 | Initial retry delay in seconds |
| `backoff_factor` | 2.0 | Exponential backoff multiplier |
| `max_delay` | 600.0 | Maximum retry delay (10 minutes) |

##  Logging

- Logs are written to both **console** and **`logs/scraper_pipeline.log`**
- Automatic log rotation when file reaches **5MB**
- Configurable log levels for different components (Selenium, urllib3, etc.)

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
