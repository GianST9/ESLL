import pyodbc
import pandas as pd
import plotly.express as px

def get_db_connection():
    server = 'scn-sql-prd'
    database = 'Marktpreise'
    username = 'saleski'
    password = 'saleski'
    port = 1433  

    conn_str = (
        f'DRIVER={{SQL Server}};'
        f'SERVER={server},{port};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        'TrustServerCertificate=yes;'
    )
    return pyodbc.connect(conn_str)

def fetch_data():
    conn = get_db_connection()
    query = """
        SELECT company_name, tariff_name, type, timestamp, ap, gp, plz
        FROM tariffs
        WHERE timestamp IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def plot_tariffs_with_dropdown(df, tariff_type):
    df_filtered = df[df['type'] == tariff_type].copy()
    if df_filtered.empty:
        print(f"No data available for tariff type: {tariff_type}")
        return

    df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'])

    # Erzeuge kombinierten Tarifnamen (Tarif + PLZ)
    df_filtered['tariff_label'] = df_filtered['tariff_name'] + ' (PLZ: ' + df_filtered['plz'] + ')'

    df_melted = df_filtered.melt(
        id_vars=['timestamp', 'company_name', 'tariff_label'],
        value_vars=['ap', 'gp'],
        var_name='price_type',
        value_name='price'
    )

    # Plot nach kombinierten Tarifen
    fig = px.line(
        df_melted,
        x='timestamp', y='price',
        color='tariff_label',
        line_dash='price_type',
        hover_data=['company_name', 'price_type'],
        title=f'{tariff_type} AP & GP over time'
    )

    buttons = []
    tariffs = df_filtered['tariff_label'].unique()
    for tariff in tariffs:
        visible = [tariff in trace.name for trace in fig.data]
        buttons.append(dict(
            label=tariff,
            method='update',
            args=[{'visible': visible},
                  {'title': f'{tariff_type} AP & GP over time - {tariff}'}]
        ))

    buttons.insert(0, dict(
        label='Alle',
        method='update',
        args=[{'visible': [True] * len(fig.data)},
              {'title': f'{tariff_type} AP & GP over time - Alle'}]
    ))

    fig.update_layout(
        updatemenus=[dict(
            active=0,
            buttons=buttons,
            x=1.15,
            y=1,
            xanchor='left',
            yanchor='top'
        )],
        xaxis_title='Date',
        yaxis_title='Price',
        legend_title_text='Tariff (PLZ)',
        template='plotly_white'
    )

    fig.show()

def main():
    df = fetch_data()
    plot_tariffs_with_dropdown(df, 'Strom')
    plot_tariffs_with_dropdown(df, 'Gas')

if __name__ == "__main__":
    main()