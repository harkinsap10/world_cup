MODEL (
  name marts.fct_wc_group_stage_results,
  kind FULL, 
  cron '@daily'
);

WITH match_outcomes AS (
  SELECT
    home_team_id AS team_id,
    score_home AS goals_for,
    score_away AS goals_against,
    CASE 
      WHEN score_home > score_away THEN 3
      WHEN score_home = score_away THEN 1
      ELSE 0
    END AS points
  FROM sqlmesh.stg_wc_matches
  
  UNION ALL
  
  SELECT
    away_team_id AS team_id,
    score_away AS goals_for,
    score_home AS goals_against,
    CASE 
      WHEN score_away > score_home THEN 3
      WHEN score_away = score_home THEN 1
      ELSE 0
    END AS points
  FROM sqlmesh.stg_wc_matches
)
SELECT
  g.group_name,
  t.team_name AS country_name,
  COUNT(*) AS games_played,
  SUM(o.goals_for) AS goals_for,
  SUM(o.goals_against) AS goals_against,
  (SUM(o.goals_for) - SUM(o.goals_against)) AS goal_difference,
  SUM(o.points) AS points
FROM match_outcomes AS o
    JOIN sqlmesh.stg_wc_teams AS t ON o.team_id = t.team_id
    JOIN sqlmesh.stg_team_groups AS g ON t.team_name = g.team
GROUP BY 1, 2
ORDER BY group_name ASC, points DESC, goal_difference DESC;