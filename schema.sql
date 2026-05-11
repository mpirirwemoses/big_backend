-- Global Patent Intelligence Data Pipeline Schema

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patents (
    patent_id TEXT PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    filing_date TEXT,
    year INTEGER
);

CREATE TABLE IF NOT EXISTS inventors (
    inventor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id TEXT NOT NULL,
    inventor_id TEXT,
    company_id TEXT,
    FOREIGN KEY (patent_id) REFERENCES patents(patent_id) ON DELETE CASCADE,
    FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_patents_year ON patents(year);
CREATE INDEX IF NOT EXISTS idx_inventors_name ON inventors(name);
CREATE INDEX IF NOT EXISTS idx_inventors_country ON inventors(country);
CREATE INDEX IF NOT EXISTS idx_relationships_patent ON relationships(patent_id);
CREATE INDEX IF NOT EXISTS idx_relationships_inventor ON relationships(inventor_id);
CREATE INDEX IF NOT EXISTS idx_relationships_company ON relationships(company_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_relationships_unique ON relationships(patent_id, inventor_id, company_id);
