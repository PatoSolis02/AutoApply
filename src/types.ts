export type ApplicationStatus =
  | 'captured'
  | 'drafting'
  | 'ready_to_apply'
  | 'applied'
  | 'interview'
  | 'rejected'
  | 'offer';

export interface ApplicationSummary {
  id: string;
  company: string;
  role_title: string;
  job_url: string;
  job_source: 'linkedin';
  location: string | null;
  status: ApplicationStatus;
  notes: string;
  fit_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface ResumeApproval {
  approved: boolean;
  approved_at: string | null;
}

export interface ResumeTimelineEntry {
  id: string;
  application_id: string;
  template_id: string;
  pdf_path: string;
  rendered_html_path: string;
  approval: ResumeApproval;
  created_at: string;
}

export interface ApplicationDetail extends ApplicationSummary {
  latest_resume_version: ResumeTimelineEntry | null;
}

export interface ResumeRewordedItem {
  from: string;
  to: string;
  reason: 'job_alignment' | 'clarity' | 'brevity';
}

export interface ResumeChangeLog {
  added: string[];
  removed: string[];
  reworded: ResumeRewordedItem[];
}

export interface ResumeClaim {
  bullet_id: string;
  bullet_text: string;
  source_type: 'experience' | 'project' | 'education' | 'skill';
  source_id: string;
  evidence_text: string;
  verification_status: 'supported' | 'rejected';
}

export interface ResumeVersionDetail extends ResumeTimelineEntry {
  render_model_json: {
    headline: string;
    summary: string;
    selected_experience_ids: string[];
    selected_project_ids: string[];
    selected_skill_keywords: string[];
    sections: {
      experience: Array<{
        entry_id: string;
        bullets: Array<{ id: string; text: string }>;
      }>;
      projects: Array<{
        entry_id: string;
        bullets: Array<{ id: string; text: string }>;
      }>;
    };
  };
  change_log: ResumeChangeLog;
  claims_map: ResumeClaim[];
}

export interface PaginatedResponse<T> {
  items: T[];
  page?: number;
  page_size?: number;
  total?: number;
}

export interface UserProfile {
  id: string;
  full_name: string;
  headline: string | null;
  summary: string | null;
  experiences: Array<Record<string, unknown>>;
  projects: Array<Record<string, unknown>>;
  skills: string[];
  education: Array<Record<string, unknown>>;
  updated_at: string;
}

export interface UpsertUserProfileRequest {
  id?: string;
  full_name: string;
  headline?: string | null;
  summary?: string | null;
  experiences?: Array<Record<string, unknown>>;
  projects?: Array<Record<string, unknown>>;
  skills?: string[];
  education?: Array<Record<string, unknown>>;
}
