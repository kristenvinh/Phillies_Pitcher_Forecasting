import os
import gspread
from gspread_dataframe import set_with_dataframe
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

def sync_bigquery_to_sheets():
    # 1. Grab environment variables
    project_id = os.getenv("GCP_PROJECT_ID")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # You will set this environment variable or paste your literal Sheet ID here
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "YOUR_ACTUAL_GOOGLE_SHEET_LONG_ID_HERE")
    
    if not project_id or not creds_path:
        raise ValueError("Missing required GCP environment variables.")

    print("Executing BigQuery feature extraction...")
    bq_client = bigquery.Client(project=project_id)
    
    # Query your feature-engineered rolling metrics view or table
    query = f"""
    SELECT 
      play_id,
      PARSE_DATE('%Y-%m-%d', game_date) AS match_date,
      player_name,
      pitch_type,
      SAFE_CAST(release_spin_rate AS FLOAT64) AS spin_rate,
      SAFE_CAST(release_speed AS FLOAT64) AS velocity
    FROM `{project_id}.baseball_data.statcast_daily_pitches`
    WHERE game_date IS NOT NULL
    ORDER BY match_date DESC
    """
    df = bq_client.query(query).to_dataframe()

    print(f"Retrieved {len(df)} rows from BigQuery. Authenticating with Google Sheets...")
    
    # 2. Authenticate with Google Sheets using the same Service Account JSON
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    gc = gspread.authorize(creds)
    
    # 3. Open the sheet and target the first worksheet tab
    spreadsheet = gc.open_by_key(sheet_id)
    worksheet = spreadsheet.get_worksheet(0) # 0 is the first tab
    
    print("Clearing existing spreadsheet data and writing fresh payload...")
    worksheet.clear()
    
    # 4. Upload dataframe smoothly including the headers
    set_with_dataframe(worksheet, df, row=1, col=1, include_column_header=True)
    print("✅ Google Sheet sync successfully completed!")

if __name__ == "__main__":
    sync_bigquery_to_sheets()