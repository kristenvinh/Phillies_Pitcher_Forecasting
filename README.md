# Phillies_Pitcher_Forecasting

Goal of this project is to detect when a Phillies Bullpen pitcher's underlying metrics (velocity, release point, spin rate) begin to drift from their baseline. This kind of "data drift" usually happens before a pitcher starts giving up runs, making it an excellent early-warning system for fatigue or hidden injury.

Created using assistance from Gemini AI. 

## Fetch_and_Load.py

This script calculates yesterday's date, fetches the pitch-by-pitch data using pybaseball, filters for the Phillies pitching staff, cleans up column names, and appends the data into a BigQuery database. If no data has been loaded yet, it loads all the data for the current season.

## BigQuery SQL Query: pitchers.sql
Run in the BigQuery interface, this query calculates each pitcher's daily average spin rate and velocity for each pitch type, its trailing 7-day moving average, and its season-long baseline up to that date.

## Daily Run Automation: dailyscrape.yaml
A GitHub Actions workflow (.github/workflows/daily_scrape.yaml) to run the Statcast ingestion pipeline daily (cron at 10:00 UTC) and via manual dispatch. The job checks out the repo, authenticates to GCP using secrets, sets up Cloud SDK, builds a Docker image (phillies-statcast-scraper) and runs the container with GCP project and credentials mounted from the runner environment to perform the daily scrape and load (fetch_and_load.py).

## Drift Detection Script: detect_drift.py
A small utility that queries Statcast pitch data from BigQuery for pitchers from the previous day's game, splits records into a historical baseline and a target game, and runs two-sample Kolmogorov–Smirnov tests on spin rate and velocity to detect distributional drift (p < 0.05). Includes simple safeguards (requires >=5 pitches in the target game) and prints actionable alerts. Defaults project from GCP_PROJECT_ID env var and provides sample pitcher, pitch code, and target date for quick local testing.

### Run the detect_drift
```bash
docker run --rm \
  -e GCP_PROJECT_ID="phillies-analytics-portfolio" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/google_creds.json" \
  -v ~/.config/gcloud/application_default_credentials.json:/app/secrets/google_creds.json \
  phillies-statcast-scraper \
  python detect_drift.py
  ```

