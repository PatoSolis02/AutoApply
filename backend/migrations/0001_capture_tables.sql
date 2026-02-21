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

CREATE TABLE IF NOT EXISTS user_profiles (
  id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  headline TEXT,
  summary TEXT,
  experiences_json TEXT NOT NULL,
  projects_json TEXT NOT NULL,
  skills_json TEXT NOT NULL,
  education_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resume_versions (
  id TEXT PRIMARY KEY,
  application_id TEXT NOT NULL,
  template_id TEXT NOT NULL,
  pdf_path TEXT NOT NULL,
  rendered_html_path TEXT NOT NULL,
  render_model_json TEXT NOT NULL,
  change_log_json TEXT NOT NULL,
  claims_map_json TEXT NOT NULL,
  approval_approved INTEGER NOT NULL DEFAULT 0,
  approval_approved_at TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resume_versions_application_id_created_at
ON resume_versions(application_id, created_at);
