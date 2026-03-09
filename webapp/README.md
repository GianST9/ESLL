# Marktpreise Dashboard

A Dash-based web application for visualizing and analyzing market prices (Marktpreise) for electricity (Strom) and gas (Gas) tariffs. The app fetches data from SQL Server databases, caches it locally in Parquet format, and provides interactive graphs, tables, and pivot views with filtering options.

## Features

- **Data Visualization**: Interactive line graphs showing price trends over time for selected tariffs and companies.
- **Filtering Options**: Filter by company, tariff, energy type (Strom/Gas), and price type (Arbeitspreis/Grundpreis).
- **Baseline Comparison**: Option to overlay baseline prices from EEX spot markets for Strom and Gas.
- **Multiple Views**: Switch between graph view, data table view, and weekly pivot table view.
- **Data Refresh**: Manual refresh button to update data from the database.
- **Caching**: Data is cached locally to improve performance; refresh forces a database query.
- **Shutdown Functionality**: Built-in shutdown button for the application.
- **Status Display**: Real-time status indicator at the bottom of the page.

## Requirements

- Python 3.8+
- SQL Server access (for data fetching)
- Required Python packages (see `requirements.txt`):
  - dash
  - pandas
  - numpy
  - plotly
  - gunicorn
  - python-dotenv
  - pyodbc
  - requests
  - fastparquet
  - flask
  - pyinstaller

## Installation

1. Clone or download the repository.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in a `.env` file (see Environment Variables section).

## Environment Variables

Create a `.env` file in the root directory with the following variables for database connections:

```
DB_SERVER=your_sql_server
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=1433
```

Note: For the Marktpreise database, credentials are hardcoded in the script (TODO: update with environment variables). For Energiewirtschaft, it uses the above env vars.

## Usage

### Running the App

To run the web application:

```
python app.py
```

The app will start a local server (default port 8050). Open a web browser and navigate to `http://127.0.0.1:8050/`.

### Using the Dashboard

1. Select companies, tariffs, energy types, and price types using the dropdowns and checklists.
2. Toggle baseline prices if desired.
3. Switch between Graph View, Table View, and Weekly Pivot Table using the tabs.
4. Click "Refresh Data" to fetch the latest data from the database.
5. Use the "Shutdown App here!" button to stop the application.

### Building the Executable

The app can be packaged into a standalone executable using PyInstaller. A spec file `Dash_MP.spec` is provided.

To build:

```
pyinstaller Dash_MP.spec
```

The executable will be created in the `build/Dash_MP/` directory.

## Data Sources

- **Tariffs Data**: Fetched from 'Marktpreise' database on SQL Server.
- **Baseline Prices**: Fetched from 'Energiewirtschaft' database, including EEX spot prices for Gas and Strom.

Data is cached in `data_cache.parquet` for performance.

## Notes

- Ensure SQL Server is accessible and credentials are correct.
- The app uses `pyodbc` for database connections; ensure the SQL Server driver is installed.
- For production deployment, consider using a WSGI server like Gunicorn.
- The shutdown functionality is intended for development/testing; remove or secure in production.

## License

[Add license information if applicable]

## Contributing

[Add contribution guidelines if applicable]
