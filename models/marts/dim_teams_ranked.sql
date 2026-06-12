MODEL (
  name sqlmesh.dim_teams_ranked,
  kind FULL,
  cron '@daily'
);

SELECT
  t.team_id,
  t.team_name,
  t.tla,
  t.crest_url,
  r.fifa_rank
FROM sqlmesh.stg_wc_teams AS t
LEFT JOIN sqlmesh.stg_wc_rankings AS r 
  ON t.team_name = r.country_name;