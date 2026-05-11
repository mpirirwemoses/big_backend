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
import numpy as np

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
        conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
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
            
            # Create tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patents (
                    patent_id TEXT PRIMARY KEY,
                    title TEXT,
                    abstract TEXT,
                    filing_date TEXT,
                    year INTEGER
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventors (
                    inventor_id TEXT PRIMARY KEY,
                    name TEXT,
                    country TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    company_id TEXT PRIMARY KEY,
                    name TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    patent_id TEXT,
                    inventor_id TEXT,
                    company_id TEXT,
                    FOREIGN KEY (patent_id) REFERENCES patents(patent_id),
                    FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id),
                    FOREIGN KEY (company_id) REFERENCES companies(company_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT
                )
            """)
            
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_relationships_unique ON relationships (patent_id, inventor_id, company_id)"
            )

            # Drop and recreate views
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
            
            # Check if database is empty and run pipeline automatically
            cursor.execute("SELECT COUNT(*) FROM patents")
            if cursor.fetchone()[0] == 0:
                print("[INFO] Database empty, checking for data files...")
                # Run pipeline in background thread to avoid blocking startup
                import threading
                threading.Thread(target=run_pipeline, daemon=True).start()
                
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
    return v.strip() if v.strip() else None

def hash_password(password):
    if not password: return None
    return hashlib.sha256(password.encode()).hexdigest()

def prepare_batch_data(df, columns=None):
    if columns: 
        df = df[columns]
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
        
        # Check if any files exist
        if not any([os.path.exists(PATENT_FILE), os.path.exists(INVENTOR_FILE), os.path.exists(ASSIGNEE_FILE)]):
            print("[WARNING] No data files found. Loading sample data for testing.")
            load_sample_data()
            return {
                "status": "success", 
                "message": "Sample data loaded (no TSV files found)",
                "total_patents": 3,
                "total_inventors": 3,
                "total_companies": 3,
                "total_relationships": 3
            }
        
        batch_size = 1000
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. Patents
            total_patents = 0
            if os.path.exists(PATENT_FILE) and os.path.exists(ABSTRACT_FILE):
                print("[INFO] Loading patents and abstracts...")
                try:
                    abstracts_df = pd.read_csv(ABSTRACT_FILE, sep="\t", low_memory=False)
                    print(f"[INFO] Loaded {len(abstracts_df)} abstracts")
                except Exception as e:
                    print(f"[ERROR] Loading abstracts: {e}")
                    abstracts_df = pd.DataFrame()
                
                clean_patents_all = []
                try:
                    for chunk in pd.read_csv(PATENT_FILE, sep="\t", chunksize=batch_size):
                        print(f"[INFO] Processing patent chunk with {len(chunk)} rows")
                        chunk = chunk[["patent_id", "patent_title", "patent_date"]].copy()
                        chunk.rename(columns={"patent_title": "title", "patent_date": "filing_date"}, inplace=True)
                        chunk["filing_date"] = pd.to_datetime(chunk["filing_date"], errors="coerce")
                        chunk["year"] = chunk["filing_date"].dt.year
                        chunk["filing_date"] = chunk["filing_date"].astype(str)
                        
                        if not abstracts_df.empty:
                            chunk = chunk.merge(abstracts_df[["patent_id", "patent_abstract"]], on="patent_id", how="left")
                            chunk["abstract"] = chunk["patent_abstract"].fillna("N/A")
                            chunk.drop(columns=["patent_abstract"], inplace=True)
                        else:
                            chunk["abstract"] = "N/A"
                        
                        chunk.drop_duplicates(subset=["patent_id"], inplace=True)
                        chunk = chunk.dropna(subset=["patent_id"])
                        
                        clean_patents_all.append(chunk)
                        patent_data = prepare_batch_data(chunk, ["patent_id", "title", "abstract", "filing_date", "year"])
                        if patent_data:
                            cursor.executemany("INSERT OR REPLACE INTO patents VALUES (?, ?, ?, ?, ?)", patent_data)
                            total_patents += len(patent_data)
                    conn.commit()
                    print(f"[INFO] Loaded {total_patents} patents")
                    
                    if clean_patents_all:
                        pd.concat(clean_patents_all).to_csv(os.path.join(BASE_DIR, "..", "clean_patents.csv"), index=False)
                except Exception as e:
                    print(f"[ERROR] Processing patents: {e}")
                    traceback.print_exc()
            
            # 2. Inventors
            total_inventors = 0
            if os.path.exists(INVENTOR_FILE):
                print("[INFO] Loading inventors...")
                clean_inventors_all = []
                try:
                    for chunk in pd.read_csv(INVENTOR_FILE, sep="\t", chunksize=batch_size):
                        chunk["name"] = (chunk.get("disambig_inventor_name_first", pd.Series()).fillna("") + " " + chunk.get("disambig_inventor_name_last", pd.Series()).fillna("")).str.strip().replace("", "Unknown")
                        chunk["country"] = "Unknown"
                        chunk = chunk[["inventor_id", "name", "country"]].drop_duplicates()
                        chunk = chunk.dropna(subset=["inventor_id"])
                        
                        clean_inventors_all.append(chunk)
                        inv_data = prepare_batch_data(chunk, ["inventor_id", "name", "country"])
                        if inv_data:
                            cursor.executemany("INSERT OR REPLACE INTO inventors VALUES (?, ?, ?)", inv_data)
                            total_inventors += len(inv_data)
                    conn.commit()
                    print(f"[INFO] Loaded {total_inventors} inventors")
                    
                    if clean_inventors_all:
                        pd.concat(clean_inventors_all).to_csv(os.path.join(BASE_DIR, "..", "clean_inventors.csv"), index=False)
                except Exception as e:
                    print(f"[ERROR] Processing inventors: {e}")
                    traceback.print_exc()
            
            # 3. Companies (Assignees)
            total_companies = 0
            if os.path.exists(ASSIGNEE_FILE):
                print("[INFO] Loading companies...")
                clean_companies_all = []
                try:
                    for chunk in pd.read_csv(ASSIGNEE_FILE, sep="\t", chunksize=batch_size):
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
                        chunk = chunk.dropna(subset=["company_id"])
                        
                        clean_companies_all.append(chunk)
                        comp_data = prepare_batch_data(chunk, ["company_id", "name"])
                        if comp_data:
                            cursor.executemany("INSERT OR REPLACE INTO companies VALUES (?, ?)", comp_data)
                            total_companies += len(comp_data)
                    conn.commit()
                    print(f"[INFO] Loaded {total_companies} companies")
                    
                    if clean_companies_all:
                        pd.concat(clean_companies_all).to_csv(os.path.join(BASE_DIR, "..", "clean_companies.csv"), index=False)
                except Exception as e:
                    print(f"[ERROR] Processing companies: {e}")
                    traceback.print_exc()

            # 4. Relationships (Inventors)
            total_relationships = 0
            if os.path.exists(REL_FILE):
                print("[INFO] Loading inventor relationships...")
                try:
                    sample_rel = pd.read_csv(REL_FILE, sep="\t", nrows=5)
                    inventor_cols = [c for c in sample_rel.columns if "disamb_inventor_id" in c]
                    inventor_col = sorted(inventor_cols)[-1] if inventor_cols else None
                    
                    if inventor_col:
                        print(f"[INFO] Using inventor column: {inventor_col}")
                        for chunk in pd.read_csv(REL_FILE, sep="\t", chunksize=batch_size):
                            if "patent_id" in chunk.columns and inventor_col in chunk.columns:
                                rel = chunk[["patent_id", inventor_col]].dropna()
                                rel_data = [(str(r[0]), str(r[1]), None) for r in rel.itertuples(index=False, name=None)]
                                if rel_data:
                                    cursor.executemany("INSERT OR IGNORE INTO relationships (patent_id, inventor_id, company_id) VALUES (?, ?, ?)", rel_data)
                                    total_relationships += len(rel_data)
                        conn.commit()
                        print(f"[INFO] Loaded {total_relationships} inventor relationships")
                except Exception as e:
                    print(f"[ERROR] Processing inventor relationships: {e}")
                    traceback.print_exc()
            
            # 5. Relationships (Companies)
            if os.path.exists(ASSIGNEE_FILE):
                print("[INFO] Loading company relationships...")
                company_rels = 0
                try:
                    for chunk in pd.read_csv(ASSIGNEE_FILE, sep="\t", chunksize=batch_size):
                        if "patent_id" in chunk.columns and "assignee_id" in chunk.columns:
                            rel = chunk[["patent_id", "assignee_id"]].dropna()
                            rel_data = [(str(r[0]), None, str(r[1])) for r in rel.itertuples(index=False, name=None)]
                            if rel_data:
                                cursor.executemany("INSERT OR IGNORE INTO relationships (patent_id, inventor_id, company_id) VALUES (?, ?, ?)", rel_data)
                                company_rels += len(rel_data)
                    conn.commit()
                    print(f"[INFO] Loaded {company_rels} company relationships")
                    total_relationships += company_rels
                except Exception as e:
                    print(f"[ERROR] Processing company relationships: {e}")
                    traceback.print_exc()
            
        print(f"[SUCCESS] PIPELINE SUCCESS - Patents: {total_patents}, Inventors: {total_inventors}, Companies: {total_companies}, Relationships: {total_relationships}")
        
        # Generate Console Report and JSON Report
        generate_reports_files()
        
        return {
            "status": "success",
            "message": f"Pipeline completed! Loaded {total_patents} patents, {total_inventors} inventors, {total_companies} companies",
            "total_patents": total_patents,
            "total_inventors": total_inventors,
            "total_companies": total_companies,
            "total_relationships": total_relationships
        }
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

def load_sample_data():
    """Load sample data for testing when TSV files are not available"""
    print("[INFO] Loading sample data...")
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Sample patents
            sample_patents = [
                ("PAT001", "Quantum Computing Patent", "A novel quantum computing approach", "2020-01-15", 2020),
                ("PAT002", "AI Healthcare System", "Machine learning for medical diagnosis", "2021-03-20", 2021),
                ("PAT003", "Blockchain Security", "Decentralized security protocol", "2022-05-10", 2022),
                ("PAT004", "5G Network Optimization", "Advanced cellular network routing", "2021-08-15", 2021),
                ("PAT005", "Electric Vehicle Battery", "Fast-charging lithium-ion technology", "2022-01-20", 2022),
                ("PAT006", "Machine Learning Algorithm", "Neural network optimization", "2020-11-30", 2020),
                ("PAT007", "Solar Panel Efficiency", "Photovoltaic cell improvements", "2021-06-10", 2021),
                ("PAT008", "Robotic Surgery System", "Precision medical robotics", "2022-09-05", 2022),
                ("PAT009", "Facial Recognition", "Biometric security system", "2020-04-25", 2020),
                ("PAT010", "Cloud Computing Platform", "Distributed computing architecture", "2021-12-12", 2021),
            ]
            cursor.executemany("INSERT OR REPLACE INTO patents VALUES (?, ?, ?, ?, ?)", sample_patents)
            
            # Sample inventors
            sample_inventors = [
                ("INV001", "John Smith", "USA"),
                ("INV002", "Maria Garcia", "Spain"),
                ("INV003", "Kenji Tanaka", "Japan"),
                ("INV004", "Sarah Johnson", "USA"),
                ("INV005", "Luis Rodriguez", "Mexico"),
                ("INV006", "Wei Chen", "China"),
                ("INV007", "Emma Brown", "UK"),
                ("INV008", "Hans Mueller", "Germany"),
                ("INV009", "Sophie Dubois", "France"),
                ("INV010", "Marco Rossi", "Italy"),
            ]
            cursor.executemany("INSERT OR REPLACE INTO inventors VALUES (?, ?, ?)", sample_inventors)
            
            # Sample companies
            sample_companies = [
                ("COM001", "Tech Corp"),
                ("COM002", "Health Innovations"),
                ("COM003", "SecureChain Ltd"),
                ("COM004", "Green Energy Solutions"),
                ("COM005", "AI Research Institute"),
                ("COM006", "Robotics International"),
                ("COM007", "Cloud Systems Inc"),
                ("COM008", "Biotech Laboratories"),
                ("COM009", "Telecom Global"),
                ("COM010", "Automotive Tech"),
            ]
            cursor.executemany("INSERT OR REPLACE INTO companies VALUES (?, ?)", sample_companies)
            
            # Sample relationships
            sample_relationships = [
                ("PAT001", "INV001", "COM001"),
                ("PAT002", "INV002", "COM002"),
                ("PAT003", "INV003", "COM003"),
                ("PAT004", "INV004", "COM009"),
                ("PAT005", "INV005", "COM004"),
                ("PAT006", "INV006", "COM005"),
                ("PAT007", "INV007", "COM004"),
                ("PAT008", "INV008", "COM006"),
                ("PAT009", "INV009", "COM007"),
                ("PAT010", "INV010", "COM010"),
            ]
            cursor.executemany("INSERT OR IGNORE INTO relationships VALUES (?, ?, ?)", sample_relationships)
            
            conn.commit()
            print("[INFO] Sample data loaded successfully (10+ rows per table)")
    except Exception as e:
        print(f"[ERROR] Loading sample data: {e}")

def get_table_data():
    """Get table data with at least 10 rows from each table"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get total counts
            cursor.execute("SELECT COUNT(*) FROM patents")
            total_patents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM inventors")
            total_inventors = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM companies")
            total_companies = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM relationships")
            total_relationships = cursor.fetchone()[0]
            
            # Get sample rows (at least 10 from each table)
            cursor.execute("SELECT * FROM patents LIMIT 10")
            patents = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM inventors LIMIT 10")
            inventors = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM companies LIMIT 10")
            companies = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM relationships LIMIT 10")
            relationships = [dict(row) for row in cursor.fetchall()]
            
            return {
                "status": "success",
                "total_counts": {
                    "patents": total_patents,
                    "inventors": total_inventors,
                    "companies": total_companies,
                    "relationships": total_relationships
                },
                "sample_data": {
                    "patents": patents,
                    "inventors": inventors,
                    "companies": companies,
                    "relationships": relationships
                }
            }
    except Exception as e:
        print(f"[ERROR] Getting table data: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

def generate_reports_files():
    try:
        with get_db() as conn:
            # Console Report
            cursor = conn.cursor()
            cursor.execute("SELECT total_patents FROM v_db_stats")
            result = cursor.fetchone()
            total_patents = result[0] if result else 0
            
            cursor.execute("SELECT name, patent_count FROM v_top_inventors LIMIT 2")
            top_inv = cursor.fetchall()
            
            cursor.execute("SELECT name, patent_count FROM v_top_companies LIMIT 1")
            top_comp = cursor.fetchall()
            
            cursor.execute("SELECT country FROM v_country_distribution LIMIT 2")
            top_countries = cursor.fetchall()
            
            print("\n================== PATENT REPORT ===================")
            print(f"Total Patents: {total_patents:,}")
            if top_inv:
                print(f"Top Inventors: " + " ".join([f"{i+1}. {r['name']} - {r['patent_count']}" for i, r in enumerate(top_inv)]))
            if top_comp:
                print(f"Top Companies: " + " ".join([f"{i+1}. {r['name']} - {r['patent_count']}" for i, r in enumerate(top_comp)]))
            if top_countries:
                print(f"Top Countries: " + " ".join([f"{i+1}. {r['country']}" for i, r in enumerate(top_countries)]))
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
            report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "report.json")
            with open(report_path, "w") as f:
                json.dump(report, f, indent=4)
            print(f"[INFO] Report saved to {report_path}")
                
    except Exception as e:
        print(f"[ERROR] Error generating reports files: {e}")
        traceback.print_exc()

def get_reports():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_patents, total_companies FROM v_db_stats")
            stats = cursor.fetchone()
            
            # Return empty data structure instead of error when no data
            if not stats or stats[0] == 0:
                return {
                    "status": "success",
                    "total_patents": 0,
                    "total_companies": 0,
                    "top_inventors": [],
                    "top_companies": [],
                    "countries": [],
                    "trends": [],
                    "ranked_inventors": [],
                    "joined_data": [],
                    "cte_results": [],
                    "message": "No data available. Run /run-pipeline to load data."
                }
            
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
                "cte_results": countries[:5] if countries else []
            }
    except Exception as e:
        print(f"[ERROR] get_reports error: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

# ================= MODIFIED ENDPOINT THAT RETURNS TABLES =================
@app.route('/run-pipeline', methods=['GET', 'POST'])
def run_pipeline_route():
    """Run pipeline and return table data with at least 10 rows from each table"""
    print("[INFO] Run pipeline endpoint called")
    
    # Run the pipeline
    pipeline_result = run_pipeline()
    
    # If pipeline failed, return error
    if pipeline_result.get("status") == "error":
        return jsonify({
            "success": False,
            "error": pipeline_result.get("message"),
            "pipeline_result": pipeline_result
        }), 500
    
    # Get the table data (with at least 10 rows per table)
    table_data = get_table_data()
    
    # Also get the reports data for analytics
    reports_data = get_reports()
    
    # Combine everything into one response
    return jsonify({
        "success": True,
        "message": pipeline_result.get("message", "Pipeline completed successfully"),
        "pipeline_stats": {
            "total_patents_loaded": pipeline_result.get("total_patents", 0),
            "total_inventors_loaded": pipeline_result.get("total_inventors", 0),
            "total_companies_loaded": pipeline_result.get("total_companies", 0),
            "total_relationships_loaded": pipeline_result.get("total_relationships", 0)
        },
        "tables": table_data,  # This contains the actual table data (10+ rows each)
        "analytics": reports_data  # This contains the view data for charts
    })

# Keep the original reports endpoint for backward compatibility
@app.route('/reports', methods=['GET'])
def reports_route():
    return jsonify(get_reports())

# Keep the debug endpoint for troubleshooting
@app.route('/debug-stats', methods=['GET'])
def debug_stats():
    """Debug endpoint to check database contents"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM patents")
            patents_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM inventors")
            inventors_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM companies")
            companies_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM relationships")
            relationships_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT * FROM patents LIMIT 3")
            sample_patents = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                "status": "success",
                "patents_count": patents_count,
                "inventors_count": inventors_count,
                "companies_count": companies_count,
                "relationships_count": relationships_count,
                "sample_patents": sample_patents,
                "database_exists": os.path.exists(DB_PATH),
                "db_path": DB_PATH
            })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/export-csv', methods=['GET'])
def export_csv():
    try:
        with get_db() as conn:
            # Check if data exists
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patents")
            if cursor.fetchone()[0] == 0:
                return jsonify({"status": "error", "message": "No data to export"}), 404
            
            top_inv = pd.read_sql_query("SELECT * FROM v_top_inventors", conn)
            top_comp = pd.read_sql_query("SELECT * FROM v_top_companies", conn)
            trends = pd.read_sql_query("SELECT * FROM v_patent_trends", conn)
            
            base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
            os.makedirs(base, exist_ok=True)
            
            top_inv.to_csv(os.path.join(base, "top_inventors.csv"), index=False)
            top_comp.to_csv(os.path.join(base, "top_companies.csv"), index=False)
            trends.to_csv(os.path.join(base, "country_trends.csv"), index=False)
            
            return jsonify({
                "status": "success",
                "message": "Exported analytical CSV files",
                "files": ["top_inventors.csv", "top_companies.csv", "country_trends.csv"]
            })
    except Exception as e:
        print(f"[ERROR] Export CSV error: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password required"}), 400
    
    email = data.get('email')
    password = hash_password(data.get('password'))
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
        return jsonify({"message": "Signup successful"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "User already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password required"}), 400
    
    email = data.get('email')
    password = hash_password(data.get('password'))
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    return jsonify({"user": dict(user), "message": "Login successful"})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "database_exists": os.path.exists(DB_PATH)})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    # Let API routes fall through to their own handlers
    if path.startswith('api/') or path in ['run-pipeline', 'reports', 'export-csv', 'debug-stats']:
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
        "api_endpoints": ["/api/health", "/api/login", "/api/signup", "/run-pipeline", "/reports", "/debug-stats"]
    })

# Initialize DB at module level
initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)