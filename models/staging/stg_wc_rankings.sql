MODEL (
  name sqlmesh.stg_wc_rankings,
  kind FULL
);

SELECT
  fifa_rank,
  country_name
FROM public.staging_wc_rankings;