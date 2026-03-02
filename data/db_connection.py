import psycopg2
def get_connection():
    conn=psycopg2.connect(
        host="localhost",
        port=5432,
        database="trading_db",
        user="trading",
        password="trading123"
    )
    return conn
    pass
if __name__=="__main__":
    conn=get_connection()
    print("Connected to TimescaleDB")
    conn.close()