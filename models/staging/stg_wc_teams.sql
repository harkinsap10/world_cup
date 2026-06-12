MODEL (
  name sqlmesh.stg_wc_teams,
  kind FULL,
  cron '@daily'
);

SELECT
    CAST(team_id AS INT) AS team_id
  , CASE
    WHEN name = 'United States' THEN 'USA'
    WHEN name = 'South Korea' THEN 'Korea Republic'
    WHEN name = 'Turkey' THEN 'Türkiye'
    WHEN name = 'Iran' THEN 'IR Iran'
    WHEN name = 'Bosnia-Herzegovina' THEN 'Bosnia and Herzegovina'
    WHEN name = 'Cape Verde Islands' THEN 'Cabo Verde'
    WHEN name = 'Ivory Coast' THEN 'Côte d''Ivoire'
    ELSE name
    END AS team_name 
  , CAST(tla AS VARCHAR) AS tla
  , CAST(crest_url AS TEXT) AS crest_url
FROM public.staging_wc_teams;