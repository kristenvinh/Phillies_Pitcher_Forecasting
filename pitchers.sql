WITH daily_pitch_metrics AS (
  SELECT
    PARSE_DATE('%Y-%m-%d', game_date) AS match_date,
    pitcher AS pitcher_id,
    player_name,
    pitch_type,
    COUNT(*) AS pitch_count,
    AVG(SAFE_CAST(release_spin_rate AS FLOAT64)) AS avg_daily_spin_rate,
    AVG(SAFE_CAST(release_speed AS FLOAT64)) AS avg_daily_velocity
  FROM
    `baseball_data.statcast_daily_pitches`
  WHERE
    pitch_type IS NOT NULL 
    AND release_spin_rate IS NOT NULL
  GROUP BY
    match_date,
    pitcher_id,
    player_name,
    pitch_type
),

rolling_metrics AS (
  SELECT
    match_date,
    pitcher_id,
    player_name,
    pitch_type,
    pitch_count,
    avg_daily_spin_rate,
    
    -- FIXED: ORDER BY uses UNIX_DATE() to turn the date into an integer number of days.
    -- This allows us to use standard integer offsets (7 and 1) instead of INTERVAL.
    AVG(avg_daily_spin_rate) OVER(
      PARTITION BY pitcher_id, pitch_type
      ORDER BY UNIX_DATE(match_date)
      RANGE BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS trailing_7d_spin_baseline,

    -- ROWS window frames don't have this restriction, so this remains unchanged
    AVG(avg_daily_spin_rate) OVER(
      PARTITION BY pitcher_id, pitch_type
      ORDER BY match_date
      ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS seasonal_spin_baseline,
    
    avg_daily_velocity,
    
    -- FIXED: Applied the same UNIX_DATE() fix for the velocity window
    AVG(avg_daily_velocity) OVER(
      PARTITION BY pitcher_id, pitch_type
      ORDER BY UNIX_DATE(match_date)
      RANGE BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS trailing_7d_velocity_baseline
  FROM
    daily_pitch_metrics
)

SELECT
  match_date,
  player_name,
  pitch_type,
  pitch_count,
  ROUND(avg_daily_spin_rate, 1) AS daily_spin,
  ROUND(trailing_7d_spin_baseline, 1) AS rolling_7d_spin,
  ROUND(seasonal_spin_baseline, 1) AS season_spin,
  ROUND(SAFE_DIVIDE(avg_daily_spin_rate - seasonal_spin_baseline, seasonal_spin_baseline) * 100, 2) AS spin_deviation_pct
FROM
  rolling_metrics
ORDER BY
  player_name,
  pitch_type,
  match_date DESC;