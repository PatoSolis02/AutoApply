import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { ApiError, captureJob } from '../lib/api';

interface CaptureFormState {
  title: string;
  company: string;
  location: string;
  jobUrl: string;
  descriptionRaw: string;
}

function initialFormState(): CaptureFormState {
  return {
    title: '',
    company: '',
    location: '',
    jobUrl: '',
    descriptionRaw: '',
  };
}

interface ValidationErrorDetail {
  field?: unknown;
  message?: unknown;
}

function readValidationErrors(payload: unknown): ValidationErrorDetail[] {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return [];
  const errors = (payload as { errors?: unknown }).errors;
  if (!Array.isArray(errors)) return [];
  return errors.filter((entry) => entry && typeof entry === 'object') as ValidationErrorDetail[];
}

function formatFieldName(raw: unknown): string {
  if (typeof raw !== 'string') return '';
  const value = raw.trim();
  if (!value) return '';
  if (value === 'description_raw') return 'description';
  if (value === 'job_url') return 'job URL';
  return value.replace(/_/g, ' ');
}

function fieldRecoveryHint(field: string): string {
  if (field === 'title') return 'Add the role title from the posting header.';
  if (field === 'company') return 'Add the company name shown near the role title.';
  if (field === 'job URL') return 'Paste the full job posting URL (LinkedIn jobs/view link preferred).';
  if (field === 'description') return 'Paste the responsibilities/requirements section from the posting.';
  if (field === 'captured at') return 'Retry capture; timestamp is generated automatically.';
  return 'Review the field value and retry.';
}

function toStructured400Message(error: ApiError): string | null {
  const errors = readValidationErrors(error.payload);
  if (errors.length === 0) return null;

  const formatted = errors
    .map((entry) => {
      const field = formatFieldName(entry.field);
      if (!field) return '';
      return `${field}: ${fieldRecoveryHint(field)}`;
    })
    .filter(Boolean);

  if (formatted.length === 0) return null;
  return `Capture payload is missing or invalid. Recovery: ${formatted.join(' ')}`;
}

function toCaptureErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Capture did not complete. Review required fields and try again.';
  }

  if (error.status === 400) {
    const structured = toStructured400Message(error);
    if (structured) return structured;
    return 'Capture payload is missing or invalid. Confirm role, company, job URL, and description.';
  }

  if (error.status === 422) {
    return 'Capture was rejected by validation. Review field formatting and submit again.';
  }

  if (error.status >= 500) {
    return 'Backend capture service is unavailable. Start or restart the API, then retry.';
  }

  return error.message;
}

export function CapturePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<CaptureFormState>(initialFormState);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof CaptureFormState>(key: K, value: CaptureFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const captured = await captureJob({
        title: form.title.trim(),
        company: form.company.trim(),
        location: form.location.trim() || null,
        job_url: form.jobUrl.trim(),
        description_raw: form.descriptionRaw.trim(),
        captured_at: new Date().toISOString(),
      });
      navigate(`/applications/${captured.application_id}`);
    } catch (err: unknown) {
      setError(toCaptureErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Layout
      title="Capture Job Posting"
      subtitle="Paste the job details once to create an application workspace and start resume review."
    >
      <section className="panel">
        <h2>Manual Capture Form</h2>
        <p className="muted">Use this when you want to recover quickly without relying on browser extension capture.</p>
        <div className="guidance-list">
          <p className="tiny muted">
            1. Add role, company, posting URL, and description. 2. Submit to create the application record. 3. Continue in
            Application Detail to generate a resume version.
          </p>
        </div>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            <span>Role Title</span>
            <input value={form.title} onChange={(event) => update('title', event.target.value)} required />
          </label>
          <label>
            <span>Company</span>
            <input value={form.company} onChange={(event) => update('company', event.target.value)} required />
          </label>
          <label>
            <span>Location</span>
            <input value={form.location} onChange={(event) => update('location', event.target.value)} />
          </label>
          <label>
            <span>Job URL</span>
            <input type="url" value={form.jobUrl} onChange={(event) => update('jobUrl', event.target.value)} required />
          </label>
          <label>
            <span>Raw Description</span>
            <textarea
              value={form.descriptionRaw}
              onChange={(event) => update('descriptionRaw', event.target.value)}
              placeholder="Paste responsibilities, requirements, and skills."
              required
            />
          </label>
          <div className="actions-row">
            <button type="submit" disabled={submitting}>
              {submitting ? 'Capturing...' : 'Capture Application'}
            </button>
            <Link className="ghost-link" to="/applications">
              Back to Applications
            </Link>
          </div>
        </form>
        {error ? (
          <div className="guidance-list">
            <p className="error">{error}</p>
            <p className="tiny muted">If this keeps failing, refresh and verify the backend API is reachable before submitting again.</p>
          </div>
        ) : null}
      </section>
    </Layout>
  );
}
