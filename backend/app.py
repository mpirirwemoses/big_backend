import json
import traceback
import math
import os
import re
import sqlite3
import hashlib
from contextlib import contextmanager
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import pandas as pd

# Resolve the dist folder relative to this file so it works on Render and locally
_BASE = os.path.dirname(os.path.abspath(__file__))
_DIST = os.path.join(_BASE, '..', 'data_cleaner', 'dist')
app = Flask(__name__, static_folder=_DIST, static_url_path='')

# ================= PRODUCTION CORS CONFIGURATION =================
FRONTEND_URL = os.environ.get('FRONTEND_URL') or os.environ.get('RENDER_EXTERNAL_URL')

allowed_origins = [FRONTEND_URL] if FRONTEND_URL else ["*"]
print(f"[INFO] FRONTEND_URL={FRONTEND_URL or 'not set'}")

CORS(
    app,
    resources={r"/*": {"origins": allowed_origins}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    supports_credentials=bool(FRONTEND_URL),
    max_age=3600
)

# ================= SQLITE DATABASE CONFIGURATION =================
DEFAULT_DB_NAME = 'patent_database.db'
requested_db_path = os.environ.get('DATABASE_PATH', DEFAULT_DB_NAME)
if os.path.isabs(requested_db_path):
    DB_PATH = requested_db_path
else:
    DB_PATH = os.path.abspath(os.path.join(_BASE, '..', requested_db_path))

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
print(f"[INFO] DATABASE_PATH={DB_PATH}")
print(f"[INFO] DATABASE_EXISTS={os.path.exists(DB_PATH)}")

@contextmanager
def get_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        yield conn
    except Exception as e:
        print(f"[ERROR] Database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def initialize_database():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schema.sql")
            with open(schema_path, "r") as f:
                schema_script = f.read()
            cursor.executescript(schema_script)

            cursor.executescript("""
                DROP VIEW IF EXISTS v_top_inventors;
                CREATE VIEW v_top_inventors AS
                SELECT i.name, COUNT(r.patent_id) as patent_count
                FROM inventors i
                JOIN relationships r ON i.inventor_id = r.inventor_id
                WHERE r.inventor_id IS NOT NULL
                GROUP BY i.inventor_id, i.name
                ORDER BY patent_count DESC LIMIT 10;
                
                DROP VIEW IF EXISTS v_top_companies;
                CREATE VIEW v_top_companies AS
                SELECT c.name, COUNT(r.patent_id) as patent_count
                FROM companies c
                JOIN relationships r ON c.company_id = r.company_id
                WHERE r.company_id IS NOT NULL
                GROUP BY c.company_id, c.name
                ORDER BY patent_count DESC LIMIT 10;

                DROP VIEW IF EXISTS v_country_distribution;
                CREATE VIEW v_country_distribution AS
                SELECT country, COUNT(*) as total
                FROM inventors
                WHERE country IS NOT NULL AND country != '' AND country != 'Unknown'
                GROUP BY country ORDER BY total DESC LIMIT 10;
                
                DROP VIEW IF EXISTS v_patent_trends;
                CREATE VIEW v_patent_trends AS
                SELECT year, COUNT(*) as total
                FROM patents
                WHERE year IS NOT NULL AND year > 0
                GROUP BY year ORDER BY year LIMIT 20;
                
                DROP VIEW IF EXISTS v_ranked_inventors;
                CREATE VIEW v_ranked_inventors AS
                WITH inventor_counts AS (
                    SELECT i.name, i.country, COUNT(r.patent_id) as patent_count,
                        ROW_NUMBER() OVER (ORDER BY COUNT(r.patent_id) DESC) as rank_position,
                        DENSE_RANK() OVER (ORDER BY COUNT(r.patent_id) DESC) as dense_rank
                    FROM inventors i
                    JOIN relationships r ON i.inventor_id = r.inventor_id
                    WHERE r.inventor_id IS NOT NULL
                    GROUP BY i.inventor_id, i.name, i.country
                )
                SELECT * FROM inventor_counts LIMIT 20;
                
                DROP VIEW IF EXISTS v_joined_data;
                CREATE VIEW v_joined_data AS
                SELECT p.patent_id, p.title, i.name as inventor_name, c.name as company_name, i.country, p.year
                FROM patents p
                LEFT JOIN relationships ri ON p.patent_id = ri.patent_id AND ri.inventor_id IS NOT NULL
                LEFT JOIN inventors i ON ri.inventor_id = i.inventor_id
                LEFT JOIN relationships rc ON p.patent_id = rc.patent_id AND rc.company_id IS NOT NULL
                LEFT JOIN companies c ON rc.company_id = c.company_id
                LIMIT 50;
                
                DROP VIEW IF EXISTS v_db_stats;
                CREATE VIEW v_db_stats AS
                SELECT 
                    (SELECT COUNT(*) FROM patents) as total_patents,
                    (SELECT COUNT(*) FROM inventors) as total_inventors,
                    (SELECT COUNT(*) FROM companies) as total_companies,
                    (SELECT COUNT(*) FROM relationships) as total_relationships;
            """)
            conn.commit()
            print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization error: {e}")
        traceback.print_exc()

def clean_value(v, max_length=4000):
    if v is None: return None
    if pd.isna(v): return None
    if isinstance(v, float) and math.isnan(v): return None
    v = str(v)
    v = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", v)
    v = v.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    if len(v) > max_length: v = v[:max_length]
    return v.strip()

def hash_password(password):
    if not password: return None
    return hashlib.sha256(password.encode()).hexdigest()

def prepare_batch_data(df, columns=None):
    if columns: df = df[columns]
    data = []
    for row in df.itertuples(index=False, name=None):
        cleaned_row = tuple(clean_value(val) for val in row)
        if any(v is not None for v in cleaned_row):
            data.append(cleaned_row)
    return data

def run_pipeline():
    try:
        print("\n[INFO] PIPELINE STARTED\n")
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        print(f"[DEBUG] BASE_DIR: {BASE_DIR}")
        print(f"[DEBUG] Working directory: {os.getcwd()}")
        
        PATENT_FILE = os.path.join(BASE_DIR, "g_patent.tsv")
        ABSTRACT_FILE = os.path.join(BASE_DIR, "g_patent_abstract.tsv")
        INVENTOR_FILE = os.path.join(BASE_DIR, "g_inventor_disambiguated.tsv")
        REL_FILE = os.path.join(BASE_DIR, "g_persistent_inventor.tsv")
        ASSIGNEE_FILE = os.path.join(BASE_DIR, "g_assignee_disambiguated.tsv")
        
        print(f"[DEBUG] PATENT_FILE exists: {os.path.exists(PATENT_FILE)}")
        print(f"[DEBUG] ABSTRACT_FILE exists: {os.path.exists(ABSTRACT_FILE)}")
        print(f"[DEBUG] INVENTOR_FILE exists: {os.path.exists(INVENTOR_FILE)}")
        print(f"[DEBUG] REL_FILE exists: {os.path.exists(REL_FILE)}")
        print(f"[DEBUG] ASSIGNEE_FILE exists: {os.path.exists(ASSIGNEE_FILE)}")
        
        # We will process chunks
        batch_size = 1000
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys=OFF")
            cursor.execute("DELETE FROM relationships")
            cursor.execute("DELETE FROM companies")
            cursor.execute("DELETE FROM inventors")
            cursor.execute("DELETE FROM patents")
            cursor.execute("PRAGMA foreign_keys=ON")
            conn.commit()
            
            # 1. Patents
            total_patents = 0
            if os.path.exists(PATENT_FILE) and os.path.exists(ABSTRACT_FILE):
                abstracts_df = pd.read_csv(ABSTRACT_FILE, sep="\t", low_memory=False, nrows=50000)
                clean_patents_all = []
                for chunk in pd.read_csv(PATENT_FILE, sep="\t", chunksize=batch_size, nrows=50000):
                    chunk = chunk[["patent_id", "patent_title", "patent_date"]].copy()
                    chunk.rename(columns={"patent_title": "title", "patent_date": "filing_date"}, inplace=True)
                    chunk["filing_date"] = pd.to_datetime(chunk["filing_date"], errors="coerce")
                    chunk["year"] = chunk["filing_date"].dt.year
                    chunk["filing_date"] = chunk["filing_date"].astype(str)
                    
                    chunk = chunk.merge(abstracts_df[["patent_id", "patent_abstract"]], on="patent_id", how="left")
                    chunk["abstract"] = chunk["patent_abstract"].fillna("N/A")
                    chunk.drop(columns=["patent_abstract"], inplace=True)
                    chunk.drop_duplicates(subset=["patent_id"], inplace=True)
                    
                    clean_patents_all.append(chunk)
                    patent_data = prepare_batch_data(chunk, ["patent_id", "title", "abstract", "filing_date", "year"])
                    cursor.executemany("INSERT OR REPLACE INTO patents VALUES (?, ?, ?, ?, ?)", patent_data)
                    total_patents += len(patent_data)
                conn.commit()
                pd.concat(clean_patents_all).to_csv(os.path.join(BASE_DIR, "..", "clean_patents.csv"), index=False)
            
            # 2. Inventors
            total_inventors = 0
            if os.path.exists(INVENTOR_FILE):
                clean_inventors_all = []
                for chunk in pd.read_csv(INVENTOR_FILE, sep="\t", chunksize=batch_size, nrows=50000):
                    chunk["name"] = (chunk["disambig_inventor_name_first"].fillna("") + " " + chunk["disambig_inventor_name_last"].fillna("")).str.strip().replace("", "Unknown")
                    chunk["country"] = "Unknown"  # location_id exists but country name not available, use default
                    chunk = chunk[["inventor_id", "name", "country"]].drop_duplicates()
                    clean_inventors_all.append(chunk)
                    inv_data = prepare_batch_data(chunk, ["inventor_id", "name", "country"])
                    cursor.executemany("INSERT OR REPLACE INTO inventors VALUES (?, ?, ?)", inv_data)
                    total_inventors += len(inv_data)
                conn.commit()
                if clean_inventors_all:
                    pd.concat(clean_inventors_all).to_csv(os.path.join(BASE_DIR, "..", "clean_inventors.csv"), index=False)
            
            # 3. Companies (Assignees)
            total_companies = 0
            if os.path.exists(ASSIGNEE_FILE):
                clean_companies_all = []
                for chunk in pd.read_csv(ASSIGNEE_FILE, sep="\t", chunksize=batch_size, nrows=50000):
                    if "assignee_id" not in chunk.columns: 
                        continue
                    # Try organization name first, fallback to individual name
                    if "disambig_assignee_organization" in chunk.columns:
                        chunk["name"] = chunk["disambig_assignee_organization"].fillna("")
                    else:
                        chunk["name"] = ""
                    
                    # If org name is empty, combine first and last name
                    empty_mask = chunk["name"].isna() | (chunk["name"] == "")
                    if empty_mask.any() and "disambig_assignee_individual_name_first" in chunk.columns:
                        first = chunk.loc[empty_mask, "disambig_assignee_individual_name_first"].fillna("")
                        last = chunk.loc[empty_mask, "disambig_assignee_individual_name_last"].fillna("")
                        chunk.loc[empty_mask, "name"] = (first + " " + last).str.strip()
                    
                    chunk["name"] = chunk["name"].str.strip().replace("", "Unknown Company")
                    chunk = chunk[["assignee_id", "name"]].drop_duplicates()
                    chunk.rename(columns={"assignee_id": "company_id"}, inplace=True)
                    clean_companies_all.append(chunk)
                    comp_data = prepare_batch_data(chunk, ["company_id", "name"])
                    cursor.executemany("INSERT OR REPLACE INTO companies VALUES (?, ?)", comp_data)
                    total_companies += len(comp_data)
                conn.commit()
                if clean_companies_all:
                    pd.concat(clean_companies_all).to_csv(os.path.join(BASE_DIR, "..", "clean_companies.csv"), index=False)

            # 4. Relationships (Inventors)
            total_relationships = 0
            if os.path.exists(REL_FILE):
                sample_rel = pd.read_csv(REL_FILE, sep="\t", nrows=5)
                # Find the most recent inventor ID column (highest date)
                inventor_cols = [c for c in sample_rel.columns if "disamb_inventor_id" in c]
                inventor_col = sorted(inventor_cols)[-1] if inventor_cols else None
                if inventor_col:
                    print(f"[INFO] Using inventor column: {inventor_col}")
                    for chunk in pd.read_csv(REL_FILE, sep="\t", chunksize=batch_size, nrows=50000):
                        rel = chunk[["patent_id", inventor_col]].dropna()
                        rel_data = [(r[0], r[1], None) for r in rel.itertuples(index=False, name=None)]
                        cursor.executemany("INSERT INTO relationships (patent_id, inventor_id, company_id) VALUES (?, ?, ?)", rel_data)
                        total_relationships += len(rel_data)
                    conn.commit()
            
            # 5. Relationships (Companies)
            if os.path.exists(ASSIGNEE_FILE):
                for chunk in pd.read_csv(ASSIGNEE_FILE, sep="\t", chunksize=batch_size, nrows=50000):
                    if "patent_id" in chunk.columns and "assignee_id" in chunk.columns:
                        rel = chunk[["patent_id", "assignee_id"]].dropna()
                        rel_data = [(r[0], None, r[1]) for r in rel.itertuples(index=False, name=None)]
                        cursor.executemany("INSERT INTO relationships (patent_id, inventor_id, company_id) VALUES (?, ?, ?)", rel_data)
                        total_relationships += len(rel_data)
                conn.commit()
            
        print(f"[SUCCESS] PIPELINE SUCCESS - Patents: {total_patents}, Inventors: {total_inventors}, Companies: {total_companies}")
        
        # Generate Console Report and JSON Report
        generate_reports_files()
        
        return {
            "status": "success",
            "message": f"Pipeline completed! Loaded {total_patents} patents, {total_inventors} inventors, {total_companies} companies",
            "total_patents": total_patents,
            "total_inventors": total_inventors,
            "total_companies": total_companies
        }
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

def generate_reports_files():
    try:
        with get_db() as conn:
            # Console Report
            cursor = conn.cursor()
            cursor.execute("SELECT total_patents FROM v_db_stats")
            total_patents = cursor.fetchone()[0]
            
            cursor.execute("SELECT name, patent_count FROM v_top_inventors LIMIT 2")
            top_inv = cursor.fetchall()
            
            cursor.execute("SELECT name, patent_count FROM v_top_companies LIMIT 1")
            top_comp = cursor.fetchall()
            
            cursor.execute("SELECT country FROM v_country_distribution LIMIT 2")
            top_countries = cursor.fetchall()
            
            print("\n================== PATENT REPORT ===================")
            print(f"Total Patents: {total_patents:,}")
            print(f"Top Inventors: " + " ".join([f"{i+1}. {r[0]} - {r[1]}" for i, r in enumerate(top_inv)]))
            print(f"Top Companies: " + " ".join([f"{i+1}. {r[0]} - {r[1]}" for i, r in enumerate(top_comp)]))
            print(f"Top Countries: " + " ".join([f"{i+1}. {r[0]}" for i, r in enumerate(top_countries)]))
            print("====================================================\n")
            
            # JSON Report
            cursor.execute("SELECT name, patent_count FROM v_top_inventors")
            ti = [{"name": r[0], "patents": r[1]} for r in cursor.fetchall()]
            
            cursor.execute("SELECT name, patent_count FROM v_top_companies")
            tc = [{"name": r[0], "patents": r[1]} for r in cursor.fetchall()]
            
            cursor.execute("SELECT country, total FROM v_country_distribution")
            cd = cursor.fetchall()
            t_inv = sum(r[1] for r in cd)
            tco = [{"country": r[0], "share": round(r[1]/t_inv, 2) if t_inv else 0} for r in cd]
            
            report = {
                "total_patents": total_patents,
                "top_inventors": ti,
                "top_companies": tc,
                "top_countries": tco
            }
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "report.json"), "w") as f:
                json.dump(report, f, indent=4)
                
    except Exception as e:
        print("Error generating reports files:", e)

def get_reports():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_patents, total_companies FROM v_db_stats")
            stats = cursor.fetchone()
            if not stats or stats[0] == 0: return {"status": "error", "message": "No data"}
            
            total_patents, total_companies = stats[0], stats[1]
            
            cursor.execute("SELECT name, patent_count FROM v_top_inventors")
            top_inventors = [{"name": r[0], "patent_count": r[1]} for r in cursor.fetchall()]
            
            cursor.execute("SELECT name, patent_count FROM v_top_companies")
            top_companies = [{"name": r[0], "patent_count": r[1]} for r in cursor.fetchall()]
            
            cursor.execute("SELECT country, total FROM v_country_distribution")
            countries = [{"country": r[0], "total": r[1]} for r in cursor.fetchall()]
            
            cursor.execute("SELECT year, total FROM v_patent_trends")
            trends = [{"year": r[0], "total": r[1]} for r in cursor.fetchall()]
            
            cursor.execute("SELECT name, country, patent_count, rank_position, dense_rank FROM v_ranked_inventors")
            ranked_inventors = [{"name": r[0], "country": r[1], "patent_count": r[2], "rank_position": r[3], "dense_rank": r[4]} for r in cursor.fetchall()]
            
            cursor.execute("SELECT patent_id, title, inventor_name, company_name, country, year FROM v_joined_data")
            joined_data = [{"patent_id": r[0], "title": r[1], "inventor_name": r[2], "company_name": r[3], "country": r[4], "year": r[5]} for r in cursor.fetchall()]
            
            return {
                "status": "success",
                "total_patents": total_patents,
                "total_companies": total_companies,
                "top_inventors": top_inventors,
                "top_companies": top_companies,
                "countries": countries,
                "trends": trends,
                "ranked_inventors": ranked_inventors,
                "joined_data": joined_data,
                "cte_results": countries[:5]
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/run-pipeline', methods=['GET'])
def run_pipeline_route():
    return jsonify(run_pipeline())

@app.route('/reports', methods=['GET'])
def reports_route():
    return jsonify(get_reports())

@app.route('/export-csv', methods=['GET'])
def export_csv():
    try:
        with get_db() as conn:
            top_inv = pd.read_sql_query("SELECT * FROM v_top_inventors", conn)
            top_comp = pd.read_sql_query("SELECT * FROM v_top_companies", conn)
            trends = pd.read_sql_query("SELECT * FROM v_patent_trends", conn)
            
            base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
            top_inv.to_csv(os.path.join(base, "top_inventors.csv"), index=False)
            top_comp.to_csv(os.path.join(base, "top_companies.csv"), index=False)
            trends.to_csv(os.path.join(base, "country_trends.csv"), index=False) # requested name
            
            return jsonify({
                "status": "success",
                "message": "Exported analytical CSV files",
                "files": ["top_inventors.csv", "top_companies.csv", "country_trends.csv"]
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email, password = data.get('email'), hash_password(data.get('password'))
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
        return jsonify({"message": "Signup successful"}), 201
    except:
        return jsonify({"error": "User already exists"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email, password = data.get('email'), hash_password(data.get('password'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
    if not user: return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"user": dict(user), "message": "Login successful"})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    # Let API routes fall through to their own handlers
    if path.startswith('api/') or path in ['run-pipeline', 'reports', 'export-csv']:
        return jsonify({"error": "API endpoint not found"}), 404
    dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data_cleaner', 'dist')
    # Serve static asset if it exists
    if path != "" and os.path.exists(os.path.join(dist, path)):
        return send_from_directory(dist, path)
    # Fallback: serve React's index.html for client-side routing
    index = os.path.join(dist, 'index.html')
    if os.path.exists(index):
        return send_from_directory(dist, 'index.html')
    return jsonify({
        "message": "Frontend not built yet. API is working!",
        "api_endpoints": ["/api/health", "/api/login", "/api/signup", "/run-pipeline", "/reports"]
    })

# Initialize DB at module level so gunicorn picks it up (not just __main__)
initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)