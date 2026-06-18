import os
import sys
import requests
import psycopg2
from psycopg2.extras import execute_values

# 1. API Configuration
API_KEY = "57eaddb60f8242e8abea97d90d08e9e6"
TEAMS_URL = "http://api.football-data.org/v4/competitions/WC/teams"
MATCHES_URL = "http://api.football-data.org/v4/competitions/WC/matches"

# 2. Database Connection (Pulls password from GitHub Action env var, falls back to hardcoded if local)
DB_PASSWORD = os.environ.get("SUPABASE_PASSWORD")

if not DB_PASSWORD:
    raise ValueError("Missing SUPABASE_PASSWORD environment variable!")

DB_PARAMS = {
    "host": "aws-0-us-east-1.pooler.supabase.com",
    "port": 6543,
    "user": "postgres.snlghlaorynxleagrlwu",
    "password": DB_PASSWORD,
    "database": "postgres"
}

def fetch_data(url):
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"❌ API Request Failed for {url} (Status {response.status_code}): {response.text}")

def setup_tables(cursor):
    print("🛠️ Creating staging tables for Teams and Matches...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging_wc_teams (
            team_id INT PRIMARY KEY,
            name VARCHAR(100),
            tla VARCHAR(10),
            crest_url TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging_wc_matches (
            match_id INT PRIMARY KEY,
            utc_date TIMESTAMP,
            status VARCHAR(50),
            matchday INT,
            stage VARCHAR(50),
            home_team_id INT,
            away_team_id INT,
            score_home INT,
            score_away INT
        );
    """)

def load_teams(cursor, data):
    teams = data.get('teams', [])
    print(f"📥 Preparing {len(teams)} teams for import...")
    values = [(t.get('id'), t.get('name'), t.get('tla'), t.get('crest')) for t in teams]
    
    insert_query = """
        INSERT INTO staging_wc_teams (team_id, name, tla, crest_url)
        VALUES %s
        ON CONFLICT (team_id) DO UPDATE SET
            name = EXCLUDED.name,
            tla = EXCLUDED.tla,
            crest_url = EXCLUDED.crest_url;
    """
    execute_values(cursor, insert_query, values)

def load_matches(cursor, data):
    matches = data.get('matches', [])
    print(f"📥 Preparing {len(matches)} matches/scores for daily update...")
    
    values = []
    for m in matches:
        score_data = m.get('score', {})
        full_time = score_data.get('fullTime', {})
        
        values.append((
            m.get('id'),
            m.get('utcDate'),
            m.get('status'),
            m.get('matchday'),
            m.get('stage'),
            m.get('homeTeam', {}).get('id'),
            m.get('awayTeam', {}).get('id'),
            full_time.get('home'),
            full_time.get('away')
        ))
    
    # This explicit DO UPDATE SET guarantees daily scores overwrite the old ones
    insert_query = """
        INSERT INTO staging_wc_matches (
            match_id, utc_date, status, matchday, stage, home_team_id, away_team_id, score_home, score_away
        ) VALUES %s
        ON CONFLICT (match_id) DO UPDATE SET
            utc_date = EXCLUDED.utc_date,
            status = EXCLUDED.status,
            matchday = EXCLUDED.matchday,
            stage = EXCLUDED.stage,
            home_team_id = EXCLUDED.home_team_id,
            away_team_id = EXCLUDED.away_team_id,
            score_home = EXCLUDED.score_home,
            score_away = EXCLUDED.score_away;
    """
    execute_values(cursor, insert_query, values)

if __name__ == "__main__":
    try:
        print("📡 Fetching raw datasets...")
        raw_teams_data = fetch_data(TEAMS_URL)
        raw_matches_data = fetch_data(MATCHES_URL)
        print("✅ Data successfully pulled from API endpoints!")
        
        print("🚀 Connecting to Supabase...")
        try:
            conn = psycopg2.connect(**DB_PARAMS)
        except Exception as conn_err:
            if "aws-0-" in DB_PARAMS["host"]:
                print("🔄 Trying alternative cluster route (aws-1)...")
                DB_PARAMS["host"] = "aws-1-us-east-1.pooler.supabase.com"
                conn = psycopg2.connect(**DB_PARAMS)
            else:
                raise conn_err
                
        cursor = conn.cursor()
        
        setup_tables(cursor)
        load_teams(cursor, raw_teams_data)
        load_matches(cursor, raw_matches_data)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("🎉 Relational World Cup database successfully updated in Supabase!")
        
    except Exception as e:
        print(f"💥 Pipeline failed: {e}")
        sys.exit(1) # THIS IS CRITICAL: Forces GitHub Action to fail if something goes wrong