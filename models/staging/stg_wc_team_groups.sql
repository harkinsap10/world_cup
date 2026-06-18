MODEL (
  name sqlmesh.stg_team_groups,
  kind FULL
);

SELECT
  team,
  group_name
FROM public.staging_teams_groups