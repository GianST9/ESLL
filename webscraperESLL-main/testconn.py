import pyodbc

def run_query():
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=scn-sql-prd,1433;"
        "DATABASE=Marktpreise;"
        "UID=saleski;"
        "PWD=saleski;"
    )

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Example query
    cursor.execute("SELECT TOP 10 * FROM tariffs")

    for row in cursor.fetchall():
        print(row)

    cursor.close()
    conn.close()

run_query()