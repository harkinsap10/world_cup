import requests
import psycopg2
from psycopg2.extras import execute_values

# 1. API Configuration (football-data.org v4)
API_KEY = "57eaddb60f8242e8abea97d90d08e9e6"
TEAMS_URL = "http://api.football-data.org/v4/competitions/WC/teams"
MATCHES_URL = "http://api.football-data.org/v4/competitions/WC/matches"

# 2. Database Connection
DB_PARAMS = {
    "host": "aws-0-us-east-1.pooler.supabase.com", # Note: If this fails, switch to "aws-1-us-east-1.pooler.supabase.com"
    "port": 6543,
    "user": "postgres.snlghlaorynxleagrlwu",
    "password": "H!3!eEMS88-%49z",
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
    
    # Teams Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging_wc_teams (
            team_id INT PRIMARY KEY,
            name VARCHAR(100),
            tla VARCHAR(10),
            crest_url TEXT
        );
    """)
    
    # Matches / Fixtures Table
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
    
    values = [
        (team.get('id'), team.get('name'), team.get('tla'), team.get('crest'))
        for team in teams
    ]
    
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
    print(f"📥 Preparing {len(matches)} matches/scores for import...")
    
    values = []
    for m in matches:
        score_data = m.get('score', {})
        full_time = score_data.get('fullTime', {})
        
        home_id = m.get('homeTeam', {}).get('id')
        away_id = m.get('awayTeam', {}).get('id')
        
        values.append((
            m.get('id'),
            m.get('utcDate'),
            m.get('status'),
            m.get('matchday'),
            m.get('stage'),
            home_id,
            away_id,
            full_time.get('home'),
            full_time.get('away')
        ))
    
    insert_query = """
        INSERT INTO staging_wc_matches (
            match_id, utc_date, status, matchday, stage, home_team_id, away_team_id, score_home, score_away
        ) VALUES %s
        ON CONFLICT (match_id) DO UPDATE SET
            status = EXCLUDED.status,
            stage = EXCLUDED.stage,
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
            # Fallback block to try the secondary cluster hostname if aws-0 routes out
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
        print("🎉 Relational World Cup database successfully loaded into Supabase!")
        
    except Exception as e:
        print(f"💥 Pipeline failed: {e}")