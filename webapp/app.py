import os
import sys
import threading
from dotenv import load_dotenv
import pandas as pd
from dash import Dash, dcc, html, Output, Input
from flask import request
from dash import dash_table



cache_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
CACHE_FILE = os.path.join(cache_dir, 'data_cache.parquet')



shutdown_triggered = False

load_dotenv()  # Load environment variables from .env

def get_db_connection_to_marktpreise():
    import pyodbc
    
    server = 'scn-sql-prd.d55.tes.local'#'#os.getenv('DB_SERVER')
    database = 'Marktpreise'
    username = ''#os.getenv('DB_USER') ##TODO: ADD CREDENTIALS HERE
    password = ''#os.getenv('DB_PASSWORD') ##TODO: ADD CREDENTIALS HERE
    port = 1433#os.getenv('DB_PORT', '1433')

    #server="scn-sql-prd.d55.tes.local"
    #port=1433
    #username=""
    #password=""
    
    conn_str = (
        f'DRIVER={{SQL Server}};'
        f'SERVER={server},{port};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        'TrustServerCertificate=yes;'
    )

    return pyodbc.connect(conn_str)

def get_db_connection_to_energiewirtschaft():
    import pyodbc
    
    server = os.getenv('DB_SERVER')
    database = 'Energiewirtschaft'
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    port = os.getenv('DB_PORT', '1433')
    #server="scn-sql-prd.d55.tes.local"
    #port=1433
    #username=""
    #password=""
    #database = 'Energiewirtschaft'
    conn_str = (
        f'DRIVER={{SQL Server}};'
        f'SERVER={server},{port};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        'TrustServerCertificate=yes;'
    )

    return pyodbc.connect(conn_str)


def fetch_data(force_refresh=False):
    import pandas as pd
    
    if not force_refresh and os.path.exists(CACHE_FILE):
        print("Loading data from cache")
        return pd.read_parquet(CACHE_FILE)
    
    print("Fetching data from database...")
    conn = get_db_connection_to_marktpreise()
    query = """
        SELECT company_name, tariff_name, type, timestamp, ap, gp, plz
        FROM tariffs
        WHERE timestamp IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()

    df.to_parquet(CACHE_FILE)
    return df


def fetch_baseline_data():
    conn = get_db_connection_to_energiewirtschaft()

    # Gas baseline
    query_gas = """
        SELECT [Date] AS timestamp, [Product], [Price]
        FROM [EEX-Spot-Gas]
        WHERE [Date] >= CONVERT(datetime, '2025-05-16 00:00:00', 120)
        ORDER BY [Date];
    """
    df_gas = pd.read_sql(query_gas, conn)
    df_gas['timestamp'] = pd.to_datetime(df_gas['timestamp'])
    df_gas['type'] = 'Gas'
    df_gas.rename(columns={'Price': 'baseline_price'}, inplace=True)

    # Strom baseline
    query_strom = """
        SELECT 
            YEAR([DateTime]) AS Year, 
            MONTH([DateTime]) AS Month, 
            DAY([DateTime]) AS Day, 
            AVG([Price]) AS MidPrice
        FROM [EEX-Spot-Strom-Auktion_DE_LU]
        GROUP BY 
            YEAR([DateTime]), 
            MONTH([DateTime]), 
            DAY([DateTime])
        ORDER BY 
            Year, 
            Month, 
            Day;
    """
    df_strom = pd.read_sql(query_strom, conn)
    df_strom['timestamp'] = pd.to_datetime(df_strom[['Year', 'Month', 'Day']])
    df_strom = df_strom[df_strom['timestamp'] >= pd.Timestamp('2025-05-16')]
    df_strom['type'] = 'Strom'
    df_strom.rename(columns={'MidPrice': 'baseline_price'}, inplace=True)
    df_strom = df_strom[['timestamp', 'baseline_price', 'type']]

    df_gas = df_gas[['timestamp', 'baseline_price', 'type']]

    conn.close()
    return pd.concat([df_gas, df_strom], ignore_index=True)
app = Dash(__name__)
server = app.server

# Initial data load (no force refresh)
df = fetch_data()
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['tariff_label'] = df['tariff_name'] + ' (PLZ: ' + df['plz'] + ')'
tariffs = df['tariff_label'].unique()
types = df['type'].unique()


# Webapp Layout
app.layout = html.Div([
    html.Div(className="site-header"),
    html.Div(
        html.Button(
            "Shutdown App here!",
            id='shutdown-button',
            n_clicks=0,
            style={
                'position': 'absolute',
                'top': '10px',
                'right': '10px',
                'background-color': 'red',
                'color': 'white',
                'padding': '10px 20px',
                'border': 'none',
                'border-radius': '5px',
                'cursor': 'pointer',
                'font-size': '16px'
            }
        ),
        style={'position': 'relative'}
    ),
    
    html.H1("Marktpreise"),

    # Dropdowns
    # for company
    dcc.Dropdown(
        options=[{'label': 'All Companies', 'value': 'Alle'}] + [{'label': c, 'value': c} for c in sorted(df['company_name'].unique())],
        value=['Alle'],
        multi=True,
        id='company-dropdown',
        placeholder='Select company name(s)...'
    ),
    # for tariff
    dcc.Dropdown(
        options=[{'label': 'All Tariffs', 'value': 'Alle'}] + [{'label': t, 'value': t} for t in tariffs],
        value=['Alle'],
        multi=True,
        id='tariff-dropdown'
    ),
    
    dcc.Checklist(
        options=[{'label': 'Strom', 'value': 'Strom'}, {'label': 'Gas', 'value': 'Gas'}],
        value=['Strom', 'Gas'],
        id='type-checklist',
        labelStyle={'display': 'inline-block', 'margin-right': '10px'}
    ),

    dcc.Checklist(
        options=[{'label': 'Arbeitspreis', 'value': 'ap'}, {'label': 'Grundpreis', 'value': 'gp'}],
        value=['ap', 'gp'],
        id='price-type-checklist',
        labelStyle={'display': 'inline-block', 'margin-right': '10px'}
    ),

    dcc.Checklist(
        options=[{'label': 'Show Strom Baseline', 'value': 'Strom'}, {'label': 'Show Gas Baseline', 'value': 'Gas'}],
        value=[],
        id='baseline-toggle-checklist',
        labelStyle={'display': 'inline-block', 'margin-right': '10px'}
    ),

    html.Button("Refresh Data", id='refresh-button', n_clicks=0, style={
        'margin': '10px',
        'padding': '10px 20px',
        'font-size': '16px',
        'cursor': 'pointer'
    }),

    # Tabs for Graph and Table
    html.Div([
        dcc.Tabs(id='view-tabs', value='graph', children=[
            dcc.Tab(label='Graph View', value='graph'),
            dcc.Tab(label='Table View', value='table'),
            dcc.Tab(label='Weekly Pivot Table', value='formatted_table'),
        ]),
        html.Div(id='tab-content', style={'marginTop': '20px'})
    ], style={'width': '100%', 'overflowX': 'auto'}),

    html.Div(id='shutdown-output'),

    dcc.Interval(id='status-interval', interval=3000, n_intervals=0),
    html.Div(id='status-display', style={
        'position': 'fixed',
        'bottom': '10px',
        'left': '10px',
        'background-color': 'lightgreen',
        'padding': '10px',
        'border-radius': '5px',
        'font-weight': 'bold'
    })
])

@app.callback(
    Output('tab-content', 'children'),
    Input('view-tabs', 'value'),
    Input('tariff-dropdown', 'value'),
    Input('type-checklist', 'value'),
    Input('price-type-checklist', 'value'),
    Input('refresh-button', 'n_clicks'),
    Input('baseline-toggle-checklist', 'value'),
    Input('company-dropdown', 'value')
)
def render_content(view_tab, selected_tariffs, selected_types, selected_price_types, refresh_clicks, selected_baselines, selected_companies):
    import plotly.graph_objects as go
    from dash import dash_table
    
    df_local = fetch_data(force_refresh=(refresh_clicks > 0))
    df_local['timestamp'] = pd.to_datetime(df_local['timestamp'])
    df_local['week'] = df_local['timestamp'].dt.strftime("W%U (%Y)")
    df_local['tariff_label'] = df_local['tariff_name'] + ' (PLZ: ' + df_local['plz'] + ')'

    # Apply filters
    filtered_df = df_local.copy()
    if 'Alle' not in selected_tariffs:
        filtered_df = filtered_df[filtered_df['tariff_label'].isin(selected_tariffs)]
    if 'Alle' not in selected_types:
        filtered_df = filtered_df[filtered_df['type'].isin(selected_types)]
    if 'Alle' not in selected_companies:
        filtered_df = filtered_df[filtered_df['company_name'].isin(selected_companies)]

    df_melted = filtered_df.melt(
        id_vars=['timestamp', 'company_name', 'tariff_label', 'type'],
        value_vars=['ap', 'gp'],
        var_name='price_type',
        value_name='price'
    )
    df_melted = df_melted[df_melted['price_type'].isin(selected_price_types)]

    if view_tab == 'graph':
        fig = go.Figure()
        for tariff in filtered_df['tariff_label'].unique():
            df_tariff = df_melted[df_melted['tariff_label'] == tariff]
            for price_type in df_tariff['price_type'].unique():
                df_line = df_tariff[df_tariff['price_type'] == price_type]
                line_style = 'solid' if price_type == 'ap' else 'dot'
                fig.add_trace(go.Scatter(
                    x=df_line['timestamp'],
                    y=df_line['price'],
                    mode='lines',
                    name=f"{tariff} - {price_type.upper()}",
                    line=dict(dash=line_style),
                    yaxis='y1',
                    legendgroup=tariff,
                    showlegend=True
                ))

        if selected_baselines:
            baseline_df = fetch_baseline_data()
            for energy_type in selected_baselines:
                df_base = baseline_df[baseline_df['type'] == energy_type]
                dash_style = 'dash' if energy_type == 'Strom' else 'dashdot'
                color = 'black' if energy_type == 'Strom' else 'firebrick'
                fig.add_trace(go.Scatter(
                    x=df_base['timestamp'],
                    y=df_base['baseline_price'],
                    mode='lines',
                    name=f"{energy_type} Baseline",
                    line=dict(dash=dash_style, color=color, width=2),
                    yaxis='y2',
                    legendgroup=f"Baseline-{energy_type}",
                    showlegend=True
                ))

        fig.update_layout(
            title="AP & GP over time",
            template='plotly_white',
            height=1000,
            yaxis=dict(title="Market Prices (AP/GP)", side='left'),
            yaxis2=dict(title="EEX Baseline Prices", side='right', overlaying='y', showgrid=False),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=10),
                title=None
            ),
            margin=dict(t=60, b=120)
        )
        return dcc.Graph(figure=fig, style={'height': '1000px'})

    elif view_tab == 'table':
        # Create a DataTable view
        return dash_table.DataTable(
            data=df_melted.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_melted.columns],
            page_size=25,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            filter_action="native",
            sort_action="native",
            export_format="xlsx",
            export_headers="display",
        )
        
    elif view_tab == 'formatted_table':


        filtered_df['week'] = filtered_df['timestamp'].dt.strftime("W%U (%Y)")

        df_melted_w = filtered_df.melt(
            id_vars=['timestamp', 'week', 'tariff_label'],
            value_vars=['ap', 'gp'],
            var_name='price_type',
            value_name='price'
        )

        # Ensure consistent sorting
        df_melted_w.sort_values(by=['tariff_label', 'price_type', 'timestamp'], inplace=True)

        # Pivot prices into weekly columns (one row per tariff per price_type)
        df_price = df_melted_w.pivot_table(
            index=['tariff_label', 'price_type'],
            columns='week',
            values='price',
            aggfunc='first'
        ).sort_index(axis=1)  # Sort weeks chronologically

        # Compute deltas
        df_delta = df_price.diff(axis=1).round(2)
        df_delta.columns = [f"{col} Δ" for col in df_delta.columns]

        # Combine prices and deltas
        df_combined = pd.concat([df_price, df_delta], axis=1)

        # Flatten index
        df_combined.reset_index(inplace=True)

        # Pivot so rows are tariff_labels, and each column is e.g. W30 AP, W30 Δ, W31 GP...
        df_final = df_combined.pivot_table(
            index='tariff_label',
            columns='price_type',
            values=df_combined.columns[2:],  # skip 'tariff_label' and 'price_type'
            aggfunc='first'
        )

        # Flatten column multi-index
        df_final.columns = [f"{week} {pt.upper()}" for (week, pt) in df_final.columns]
        df_final.reset_index(inplace=True)

        # Round and format
        df_display = df_final.round(2).fillna("N/A")

        #  always show 'energis' first ----
        df_display['sort_key'] = df_display['tariff_label'].apply(
            lambda x: 0 if 'energis' in x.lower() else 1
        )
        df_display = df_display.sort_values(['sort_key', 'tariff_label']).drop(columns=['sort_key'])
        
        
        # Conditional styling
        style_data_conditional = []
        for col in df_display.columns:
            if "Δ" in col:
                style_data_conditional.extend([
                    {
                        'if': {'column_id': col,
                            'filter_query': f'{{{col}}} != "N/A" && {{{col}}} < 0'},
                        'backgroundColor': '#f8d7da',  # red for negative deltas
                        'color': 'black'
                    },
                    {
                        'if': {'column_id': col,
                            'filter_query': f'{{{col}}} != "N/A" && {{{col}}} > 0'},
                        'backgroundColor': '#d4edda',  # green for positive deltas
                        'color': 'black'
                    }
                ])

        return dash_table.DataTable(
            data=df_display.to_dict('records'),
            columns=[{"name": col, "id": col} for col in df_display.columns],
            style_table={
                'overflowX': 'auto',
                'overflowY': 'auto',
                'maxHeight': '800px',
                'width': '100%',
                'minWidth': '100%',
            },
            style_cell={'textAlign': 'center', 'color': 'black', 'backgroundColor': 'white'},
            style_header={'backgroundColor': '#dceeff', 'fontWeight': 'bold'},
            style_data_conditional=style_data_conditional,
            page_size=20,
            export_format='xlsx',
            export_headers='display',
            fixed_columns={'headers': True, 'data': 1},
        )
    return fig

@server.route('/shutdown', methods=['POST'])
def shutdown():
    import os, time
    time.sleep(3)
    #os._exit(0)

@app.callback(
    Output('shutdown-output', 'children'),
    Input('shutdown-button', 'n_clicks')
)
def shutdown_app(n_clicks):
    import requests
    global shutdown_triggered
    if n_clicks > 0 and not shutdown_triggered:
        shutdown_triggered = True
        threading.Timer(3, lambda: requests.post('http://127.0.0.1:8050/shutdown')).start()
        return
    return

@app.callback(
    Output('status-display', 'children'),
    Input('status-interval', 'n_intervals')
)
def update_status(n):
    if not shutdown_triggered:
        return "App is running, please click the shut down button."
    else:
        return "App is offline."

def auto_shutdown(delay=1000):
    import requests, time
    global shutdown_triggered
    time.sleep(delay)
    #shutdown_triggered = True ##### AUTO SHUTDOWN
    threading.Timer(3, lambda: requests.post('http://127.0.0.1:8050/shutdown')).start()

def open_browser():
    import webbrowser
    webbrowser.open_new("http://127.0.0.1:8050/")  # in network reachable at 10.216.136.96:80

if __name__ == '__main__':
    #threading.Thread(target=auto_shutdown, args=(600,), daemon=True).start()
    threading.Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=8050, debug=False)
    
    
    
    
    
# compiling to one file
"""
python -m PyInstaller --name Dash_MP --onefile --noconsole --add-data "data_cache.parquet;." --add-data "assets;assets" --hidden-import pyodbc --hidden-import pandas --hidden-import plotly --hidden-import dash_table app_plotting.py
"""
# directory version
"""
python -m PyInstaller --name Dash_MP_dir --onedir --noconsole --add-data "data_cache.parquet;." --add-data "assets;assets" --hidden-import pyodbc --hidden-import pandas --hidden-import plotly --hidden-import dash_table app_plotting.py
"""