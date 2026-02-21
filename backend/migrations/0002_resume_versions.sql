CREATE TABLE IF NOT EXISTS resume_versions (
  id TEXT PRIMARY KEY,
  application_id TEXT NOT NULL,
  template_id TEXT NOT NULL,
  pdf_path TEXT NOT NULL,
  rendered_html_path TEXT NOT NULL,
  render_model_json TEXT NOT NULL,
  change_log TEXT NOT NULL,
  claims_map TEXT NOT NULL,
  approval_approved INTEGER NOT NULL DEFAULT 0 CHECK (approval_approved IN (0, 1)),
  approval_approved_at TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resume_versions_application_id ON resume_versions(application_id);
