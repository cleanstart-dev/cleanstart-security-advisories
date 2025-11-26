import pandas as pd
from sqlalchemy import create_engine, inspect
import psycopg2
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ====== CONFIGURATION ======
SQLITE_PATH = '/home/chirag_prajapati/scan/data/vulnstatus.db'  
#SQLITE_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "scan", "data", "vulnstatus.db")
  # ← change this
PG_HOST = "34.68.11.148"                  # ← e.g., "db.company.com"
PG_PORT = "5432"
PG_DB = "postgres"
PG_USER = "postgres"
PG_PASSWORD = "triam123"

# ====== CONNECTIONS ======
sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
pg_engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")

# ====== MAIN SYNC LOGIC ======
def sync_sqlite_to_postgres():
    sqlite_inspector = inspect(sqlite_engine)
    tables = sqlite_inspector.get_table_names()
    print(f"Found {len(tables)} tables in SQLite: {tables}")

    for table_name in tables:
        print(f"\n Syncing table: {table_name}")

        # Read table from SQLite
        df = pd.read_sql_table(table_name, sqlite_engine)

        # Push to PostgreSQL (replace old data)
        df.to_sql(table_name, pg_engine, if_exists='replace', index=False)

        print(f"{len(df)} rows synced to PostgreSQL table '{table_name}'")

    print("\n Sync complete!")

if __name__ == "__main__":
    sync_sqlite_to_postgres()
