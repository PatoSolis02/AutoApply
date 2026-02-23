import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Unable to capture this job posting right now.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Layout
      title="Capture Job"
      subtitle="Create an application from a posting so tailoring and compliance workflow can begin."
    >
      <section className="panel">
        <h2>LinkedIn Capture Payload</h2>
        <p className="muted">This mirrors the `/api/v1/jobs/capture` contract used by extension capture.</p>
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
          </div>
        </form>
        {error ? <p className="error">{error}</p> : null}
      </section>
    </Layout>
  );
}
