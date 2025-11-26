import pandas as pd
from sqlalchemy import create_engine, inspect
from google.cloud import bigquery

# ====== CONFIGURATION ======
SQLITE_PATH = r"C:\path\to\your\database.db"  # <-- path to your SQLite DB
BQ_PROJECT_ID = "your-gcp-project-id"         # <-- GCP project ID
BQ_DATASET = "your_bigquery_dataset"          # <-- target BigQuery dataset

# ====== SETUP ======
sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}")
bq_client = bigquery.Client(project=BQ_PROJECT_ID)

# ====== MAIN SYNC FUNCTION ======
def sync_sqlite_to_bigquery():
    inspector = inspect(sqlite_engine)
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables in SQLite: {tables}")

    for table_name in tables:
        print(f"\n🔄 Syncing table: {table_name}")
        df = pd.read_sql_table(table_name, sqlite_engine)

        # Define target table reference
        table_id = f"{BQ_PROJECT_ID}.{BQ_DATASET}.{table_name}"

        # Upload data to BigQuery
        job = bq_client.load_table_from_dataframe(
            df,
            table_id,
            job_config=bigquery.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE",  # replaces existing table
            ),
        )
        job.result()  # wait for job to complete

        print(f"✅ {len(df)} rows synced to BigQuery table '{table_name}'")

    print("\n🎉 Sync complete!")

if __name__ == "__main__":
    sync_sqlite_to_bigquery()
