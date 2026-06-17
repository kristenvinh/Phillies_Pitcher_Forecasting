import os
import pandas as pd
from google.cloud import bigquery
from scipy import stats
from datetime import datetime, timedelta

def get_yesterdays_active_pitchers(client, project_id, target_date):
    """Finds all unique pitchers and pitch types thrown on the target date."""
    query = f"""
    SELECT DISTINCT player_name, pitch_type
    FROM `{project_id}.baseball_data.statcast_daily_pitches`
    WHERE PARSE_DATE('%Y-%m-%d', game_date) = '{target_date}'
      AND pitch_type IS NOT NULL
    """
    df = client.query(query).to_dataframe()
    # Return a list of tuples: [('Kerkering, Orion', 'ST'), ('Bowlan, Jonathan', 'FF'), ...]
    return list(df.itertuples(index=False, name=None))

def fetch_pitch_history(client, project_id, pitcher_name, pitch_type):
    """Pulls all historical pitches for a specific pitcher and pitch type."""
    query = f"""
    SELECT 
      PARSE_DATE('%Y-%m-%d', game_date) AS match_date,
      SAFE_CAST(release_spin_rate AS FLOAT64) AS spin_rate,
      SAFE_CAST(release_speed AS FLOAT64) AS velocity
    FROM `{project_id}.baseball_data.statcast_daily_pitches`
    WHERE player_name = '{pitcher_name}' 
      AND pitch_type = '{pitch_type}'
      AND release_spin_rate IS NOT NULL
      AND release_speed IS NOT NULL
    """
    return client.query(query).to_dataframe()

def analyze_drift(df, target_date_str):
    """Runs K-S tests comparing yesterday's performance to the historical baseline."""
    target_date = pd.to_datetime(target_date_str).date()
    
    baseline_df = df[df['match_date'] < target_date]
    current_df = df[df['match_date'] == target_date]
    
    # We need a minimum sample size (at least 5 pitches) to run a meaningful K-S test
    if len(current_df) < 5 or len(baseline_df) < 20:
        return None
        
    # Run statistical tests
    _, p_val_spin = stats.ks_2samp(baseline_df['spin_rate'], current_df['spin_rate'])
    _, p_val_vel = stats.ks_2samp(baseline_df['velocity'], current_df['velocity'])
    
    return {
        "pitches_thrown": len(current_df),
        "p_val_spin": p_val_spin,
        "p_val_vel": p_val_vel,
        "spin_drift": p_val_spin < 0.05,
        "vel_drift": p_val_vel < 0.05
    }

if __name__ == "__main__":
    PROJECT = os.getenv("GCP_PROJECT_ID", "your-project-id")
    bq_client = bigquery.Client(project=PROJECT)
    
    # Default to analyzing yesterday's game
    YESTERDAY = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"Scanning for performance drift from games on: {YESTERDAY}")
    active_pairs = get_yesterdays_active_pitchers(bq_client, PROJECT, YESTERDAY)
    
    if not active_pairs:
        print("No active pitchers found for yesterday. Scaling down.")
        exit(0)
        
    print(f"Found {len(active_pairs)} distinct pitcher/pitch-type profiles to analyze.\n")
    
    alerts_triggered = 0
    for pitcher, pitch_type in active_pairs:
        pitch_df = fetch_pitch_history(bq_client, PROJECT, pitcher, pitch_type)
        results = analyze_drift(pitch_df, YESTERDAY)
        
        if results:
            print(f"📊 {pitcher} ({pitch_type}) - Pitches: {results['pitches_thrown']}")
            # ... (the rest of the alert prints)
        else:
            print(f"➖ {pitcher} ({pitch_type}) - Skipped (Sample size too small)")
        
        if results:
            print(f"📊 {pitcher} ({pitch_type}) - Pitches: {results['pitches_thrown']}")
            
            if results['spin_drift']:
                print(f"  ⚠️ ALERT: Spin drift detected! (p-value: {results['p_val_spin']:.4f})")
                alerts_triggered += 1
            if results['vel_drift']:
                print(f"  ⚠️ ALERT: Velocity drift detected! (p-value: {results['p_val_vel']:.4f})")
                alerts_triggered += 1
                
            if not results['spin_drift'] and not results['vel_drift']:
                print("  ✅ Metrics stable.")
                
    print(f"\nAnalysis complete. Total anomalies flagged: {alerts_triggered}")