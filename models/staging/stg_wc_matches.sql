MODEL (
  name sqlmesh.stg_wc_matches,
  kind FULL,
  cron '@daily'
);

SELECT
    CAST(match_id AS INT) AS match_id
  , CAST(utc_date AS TIMESTAMP) AS utc_date
  , CAST(status AS VARCHAR) AS status
  , CAST(matchday AS INT) AS matchday
  , CAST(stage AS VARCHAR) AS stage
  , CAST(home_team_id AS INT) AS home_team_id
  , CAST(away_team_id AS INT) AS away_team_id
  , CAST(score_home AS INT) AS score_home
  , CAST(score_away AS INT) AS score_away
FROM public.staging_wc_matches;