# Phillies_Pitcher_Forecasting

Goal of this project is to detect when a Phillies Bullpen pitcher's underlying metrics (velocity, release point, spin rate) begin to drift from their baseline. This kind of "data drift" usually happens before a pitcher starts giving up runs, making it an excellent early-warning system for fatigue or hidden injury.

Created using assistance from Gemini AI. 

## Fetch_and_Load.py

This script calculates yesterday's date, fetches the pitch-by-pitch data using pybaseball, filters for the Phillies pitching staff, cleans up column names, and appends the data into a BigQuery database. If no data has been loaded yet, it loads all the data for the current season.

### Build Docker Image

```bash
docker build -t phillies-statcast-scraper .
```

### One-Time Backfill of Data

```bash
docker run --rm \
  -e GCP_PROJECT_ID="phillies-analytics-portfolio" \
  -v ~/.config/gcloud/application_default_credentials.json:/app/secrets/google_creds.json \
  phillies-statcast-scraper \
  python fetch_and_load.py --start "2026-03-25" --end "2026-06-10"
```

### Daily Cron Job

```bash
docker run --rm \
  -e GCP_PROJECT_ID="phillies-analytics-portfolio" \
  -v ~/.config/gcloud/application_default_credentials.json:/app/secrets/google_creds.json \
  phillies-statcast-scraper
  ```