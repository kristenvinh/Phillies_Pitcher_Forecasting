import os
import argparse
from datetime import datetime, timedelta
import pandas as pd
from google.cloud import bigquery
from pybaseball import statcast

def get_statcast_data(start_dt, end_dt):
    print(f"Fetching Statcast data from {start_dt} to {end_dt}...")
    
    # statcast() automatically handles pagination for larger date ranges
    df = statcast(start_dt=start_dt, end_dt=end_dt)
    
    if df.empty:
        print("No pitch data found for this date range.")
        return None
        
    # Filter strictly for Phillies pitching
    phillies_df = df[(df['home_team'] == 'PHI') | (df['away_team'] == 'PHI')]
    phillies_pitching = phillies_df[
        ((phillies_df['home_team'] == 'PHI') & (phillies_df['inning_topbot'] == 'Top')) |
        ((phillies_df['away_team'] == 'PHI') & (phillies_df['inning_topbot'] == 'Bot'))
    ]
    
    print(f"Retrieved {len(phillies_pitching)} pitches thrown by Phillies pitchers.")
    return phillies_pitching

def load_to_bigquery(df):
    if df is None or df.empty:
        return

    # Silenced the Pandas4Warning by explicitly targeting both object and string types
    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].astype(str)

    # Forced the project variable directly into the BigQuery initializer
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable is missing!")
        
    client = bigquery.Client(project=project_id)

    table_ref = f"{os.getenv('GCP_PROJECT_ID')}.baseball_data.statcast_daily_pitches"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=True, 
    )

    print(f"Loading data into {table_ref}...")
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result() 
    print("Database sync complete.")

if __name__ == "__main__":
    # Set up argument parsing to allow manual date overrides
    parser = argparse.ArgumentParser(description="Statcast to BigQuery Ingestion")
    parser.add_argument('--start', type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    # Default to "yesterday" if no arguments are provided
    if not args.start or not args.end:
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = yesterday_str
        end_date = yesterday_str
    else:
        start_date = args.start
        end_date = args.end

    data = get_statcast_data(start_date, end_date)
    load_to_bigquery(data)