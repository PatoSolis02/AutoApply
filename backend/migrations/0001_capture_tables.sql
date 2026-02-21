CREATE TABLE IF NOT EXISTS applications (
  id TEXT PRIMARY KEY,
  company TEXT NOT NULL,
  role_title TEXT NOT NULL,
  job_url TEXT NOT NULL,
  job_source TEXT NOT NULL CHECK (job_source = 'linkedin'),
  location TEXT,
  status TEXT NOT NULL,
  notes TEXT NOT NULL DEFAULT '',
  fit_score REAL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_postings (
  id TEXT PRIMARY KEY,
  application_id TEXT NOT NULL,
  raw_text TEXT NOT NULL,
  structured_json TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_job_postings_application_id ON job_postings(application_id);
