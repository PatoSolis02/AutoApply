import { ChangeEvent, FormEvent, useEffect, useState } from 'react';
import { AsyncBlock } from '../components/AsyncBlock';
import { Layout } from '../components/Layout';
import { ApiError, getUserProfile, upsertUserProfile } from '../lib/api';
import { UserProfile } from '../types';

interface ProfileFormState {
  id: string;
  fullName: string;
  headline: string;
  summary: string;
  skillsText: string;
  experiencesJson: string;
  projectsJson: string;
  educationJson: string;
}

function emptyForm(): ProfileFormState {
  return {
    id: 'primary',
    fullName: '',
    headline: '',
    summary: '',
    skillsText: '',
    experiencesJson: '[]',
    projectsJson: '[]',
    educationJson: '[]',
  };
}

function toFormState(profile: UserProfile): ProfileFormState {
  return {
    id: profile.id || 'primary',
    fullName: profile.full_name || '',
    headline: profile.headline || '',
    summary: profile.summary || '',
    skillsText: profile.skills.join('\n'),
    experiencesJson: JSON.stringify(profile.experiences ?? [], null, 2),
    projectsJson: JSON.stringify(profile.projects ?? [], null, 2),
    educationJson: JSON.stringify(profile.education ?? [], null, 2),
  };
}

function parseObjectArray(name: string, value: string): Array<Record<string, unknown>> {
  const trimmed = value.trim();
  if (!trimmed) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error(`${name} must be valid JSON array text.`);
  }
  if (!Array.isArray(parsed) || parsed.some((item) => item === null || typeof item !== 'object' || Array.isArray(item))) {
    throw new Error(`${name} must be a JSON array of objects.`);
  }
  return parsed as Array<Record<string, unknown>>;
}

function parseSkills(value: string): string[] {
  return value
    .split(/\n|,/)
    .map((skill) => skill.trim())
    .filter(Boolean);
}

export function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState<ProfileFormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [selectedResumeName, setSelectedResumeName] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    getUserProfile()
      .then((profile) => {
        if (!active) return;
        setForm(toFormState(profile));
      })
      .catch((err: unknown) => {
        if (!active) return;
        if (err instanceof ApiError && err.status === 404) {
          setNotice('No profile saved yet. Fill this form and click Save Profile.');
          return;
        }
        setLoadError(err instanceof Error ? err.message : 'Unable to load profile.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  function updateForm<K extends keyof ProfileFormState>(key: K, value: ProfileFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setSubmitError(null);
    setNotice(null);

    try {
      const experiences = parseObjectArray('Experiences', form.experiencesJson);
      const projects = parseObjectArray('Projects', form.projectsJson);
      const education = parseObjectArray('Education', form.educationJson);

      const profile = await upsertUserProfile({
        id: form.id || 'primary',
        full_name: form.fullName.trim(),
        headline: form.headline.trim() || null,
        summary: form.summary.trim() || null,
        skills: parseSkills(form.skillsText),
        experiences,
        projects,
        education,
      });

      setForm(toFormState(profile));
      setNotice('Profile saved. Resume generation can now use this data.');
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : 'Unable to save profile.');
    } finally {
      setSaving(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      setSelectedResumeName(null);
      return;
    }
    setSelectedResumeName(file.name);
    setNotice('Resume upload parsing is a placeholder in this sprint. Use text fields/JSON below for now.');
  }

  return (
    <Layout
      title="Profile Builder"
      subtitle="Store your resume source data: identity, summary, skills, and structured history."
    >
      <AsyncBlock loading={loading} error={loadError} loadingLabel="Loading profile...">
        <section className="panel">
          <h2>Candidate Profile</h2>
          <p className="muted">
            This data feeds resume generation and compliance checks. <code>full_name</code> is required for generation.
          </p>

          <form className="form-grid" onSubmit={handleSave}>
            <label>
              <span>Profile ID</span>
              <input value={form.id} onChange={(event) => updateForm('id', event.target.value)} />
            </label>

            <label>
              <span>Full Name (required)</span>
              <input
                value={form.fullName}
                onChange={(event) => updateForm('fullName', event.target.value)}
                placeholder="Taylor Dev"
                required
              />
            </label>

            <label>
              <span>Headline</span>
              <input
                value={form.headline}
                onChange={(event) => updateForm('headline', event.target.value)}
                placeholder="Backend Engineer"
              />
            </label>

            <label>
              <span>Summary</span>
              <textarea
                value={form.summary}
                onChange={(event) => updateForm('summary', event.target.value)}
                placeholder="2-4 lines about your experience and focus areas."
              />
            </label>

            <label>
              <span>Skills (newline or comma separated)</span>
              <textarea
                value={form.skillsText}
                onChange={(event) => updateForm('skillsText', event.target.value)}
                placeholder={'Python\nFastAPI\nSQL'}
              />
            </label>

            <label>
              <span>Experiences JSON (array of objects)</span>
              <textarea value={form.experiencesJson} onChange={(event) => updateForm('experiencesJson', event.target.value)} />
            </label>

            <label>
              <span>Projects JSON (array of objects)</span>
              <textarea value={form.projectsJson} onChange={(event) => updateForm('projectsJson', event.target.value)} />
            </label>

            <label>
              <span>Education JSON (array of objects)</span>
              <textarea value={form.educationJson} onChange={(event) => updateForm('educationJson', event.target.value)} />
            </label>

            <div className="actions-row">
              <button type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save Profile'}
              </button>
            </div>
          </form>

          {notice ? <p className="notice">{notice}</p> : null}
          {submitError ? <p className="error">{submitError}</p> : null}
        </section>

        <section className="panel">
          <h2>Resume Upload Placeholder</h2>
          <p className="muted">
            Upload parsing is not wired yet. This control is included so we can hook in resume ingestion in a later sprint.
          </p>
          <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={handleFileChange} />
          {selectedResumeName ? <p className="tiny muted">Selected: {selectedResumeName}</p> : null}
          <div className="actions-row">
            <button type="button" disabled>
              Parse Resume (coming soon)
            </button>
          </div>
        </section>
      </AsyncBlock>
    </Layout>
  );
}
