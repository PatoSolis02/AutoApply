import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';
import { AsyncBlock } from '../components/AsyncBlock';
import { DiagnosticsPanel } from '../components/DiagnosticsPanel';
import { Layout } from '../components/Layout';
import { ApiError, getUserProfile, uploadResumeToProfile, upsertUserProfile } from '../lib/api';
import { ProfileEducation, ProfileExperience, ProfileProject, UpsertUserProfileRequest, UserProfile } from '../types';

interface ExperienceFormState {
  id: string;
  company: string;
  title: string;
  startDate: string;
  endDate: string;
  bulletsText: string;
  skillsText: string;
}

interface ProjectFormState {
  id: string;
  name: string;
  description: string;
  bulletsText: string;
  skillsText: string;
  url: string;
}

interface EducationFormState {
  id: string;
  school: string;
  degree: string;
  field: string;
  startDate: string;
  endDate: string;
}

interface ProfileFormState {
  id: string;
  fullName: string;
  headline: string;
  summary: string;
  skillsText: string;
  experiences: ExperienceFormState[];
  projects: ProjectFormState[];
  education: EducationFormState[];
}

function emptyExperience(): ExperienceFormState {
  return {
    id: '',
    company: '',
    title: '',
    startDate: '',
    endDate: '',
    bulletsText: '',
    skillsText: '',
  };
}

function emptyProject(): ProjectFormState {
  return {
    id: '',
    name: '',
    description: '',
    bulletsText: '',
    skillsText: '',
    url: '',
  };
}

function emptyEducation(): EducationFormState {
  return {
    id: '',
    school: '',
    degree: '',
    field: '',
    startDate: '',
    endDate: '',
  };
}

function emptyForm(): ProfileFormState {
  return {
    id: 'primary',
    fullName: '',
    headline: '',
    summary: '',
    skillsText: '',
    experiences: [emptyExperience()],
    projects: [emptyProject()],
    education: [emptyEducation()],
  };
}

function parseDelimitedList(value: string): string[] {
  return value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function toDelimitedList(value: unknown): string {
  if (!Array.isArray(value)) return '';
  return value
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean)
    .join('\n');
}

function optionalString(value: unknown): string {
  if (typeof value !== 'string') return '';
  return value.trim();
}

function toExperienceForm(entry: ProfileExperience): ExperienceFormState {
  return {
    id: optionalString(entry.id),
    company: optionalString(entry.company),
    title: optionalString(entry.title),
    startDate: optionalString(entry.start_date),
    endDate: optionalString(entry.end_date),
    bulletsText: toDelimitedList(entry.bullets),
    skillsText: toDelimitedList(entry.skills),
  };
}

function toProjectForm(entry: ProfileProject): ProjectFormState {
  return {
    id: optionalString(entry.id),
    name: optionalString(entry.name),
    description: optionalString(entry.description),
    bulletsText: toDelimitedList(entry.bullets),
    skillsText: toDelimitedList(entry.skills),
    url: optionalString(entry.url),
  };
}

function toEducationForm(entry: ProfileEducation): EducationFormState {
  return {
    id: optionalString(entry.id),
    school: optionalString(entry.school),
    degree: optionalString(entry.degree),
    field: optionalString(entry.field),
    startDate: optionalString(entry.start_date),
    endDate: optionalString(entry.end_date),
  };
}

function ensureAtLeastOne<T>(values: T[], fallback: () => T): T[] {
  return values.length > 0 ? values : [fallback()];
}

function toFormState(profile: Partial<UserProfile>): ProfileFormState {
  return {
    id: profile.id?.trim() || 'primary',
    fullName: profile.full_name?.trim() || '',
    headline: profile.headline?.trim() || '',
    summary: profile.summary?.trim() || '',
    skillsText: toDelimitedList(profile.skills),
    experiences: ensureAtLeastOne((profile.experiences ?? []).map((entry) => toExperienceForm(entry)), emptyExperience),
    projects: ensureAtLeastOne((profile.projects ?? []).map((entry) => toProjectForm(entry)), emptyProject),
    education: ensureAtLeastOne((profile.education ?? []).map((entry) => toEducationForm(entry)), emptyEducation),
  };
}

function trimOrNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function toExperiencePayload(entry: ExperienceFormState): ProfileExperience | null {
  const experience: ProfileExperience = {};
  const hasCoreFields = Boolean(entry.id.trim() || entry.company.trim() || entry.title.trim() || entry.startDate.trim());
  if (entry.id.trim()) experience.id = entry.id.trim();
  if (entry.company.trim()) experience.company = entry.company.trim();
  if (entry.title.trim()) experience.title = entry.title.trim();
  if (entry.startDate.trim()) experience.start_date = entry.startDate.trim();
  if (entry.endDate.trim() || hasCoreFields) {
    experience.end_date = trimOrNull(entry.endDate);
  }
  const bullets = parseDelimitedList(entry.bulletsText);
  const skills = parseDelimitedList(entry.skillsText);
  if (bullets.length > 0) experience.bullets = bullets;
  if (skills.length > 0) experience.skills = skills;

  return Object.keys(experience).length > 0 ? experience : null;
}

function toProjectPayload(entry: ProjectFormState): ProfileProject | null {
  const project: ProfileProject = {};
  const hasCoreFields = Boolean(entry.id.trim() || entry.name.trim() || entry.description.trim());
  if (entry.id.trim()) project.id = entry.id.trim();
  if (entry.name.trim()) project.name = entry.name.trim();
  if (entry.description.trim()) project.description = entry.description.trim();
  const bullets = parseDelimitedList(entry.bulletsText);
  const skills = parseDelimitedList(entry.skillsText);
  if (bullets.length > 0) project.bullets = bullets;
  if (skills.length > 0) project.skills = skills;
  if (entry.url.trim() || hasCoreFields) {
    project.url = trimOrNull(entry.url);
  }

  return Object.keys(project).length > 0 ? project : null;
}

function toEducationPayload(entry: EducationFormState): ProfileEducation | null {
  const education: ProfileEducation = {};
  const hasCoreFields = Boolean(entry.id.trim() || entry.school.trim() || entry.degree.trim());
  if (entry.id.trim()) education.id = entry.id.trim();
  if (entry.school.trim()) education.school = entry.school.trim();
  if (entry.degree.trim()) education.degree = entry.degree.trim();
  if (entry.field.trim() || hasCoreFields) {
    education.field = trimOrNull(entry.field);
  }
  if (entry.startDate.trim() || hasCoreFields) {
    education.start_date = trimOrNull(entry.startDate);
  }
  if (entry.endDate.trim() || hasCoreFields) {
    education.end_date = trimOrNull(entry.endDate);
  }

  return Object.keys(education).length > 0 ? education : null;
}

function toProfilePayload(form: ProfileFormState): UpsertUserProfileRequest {
  return {
    id: form.id.trim() || 'primary',
    full_name: form.fullName.trim(),
    headline: trimOrNull(form.headline),
    summary: trimOrNull(form.summary),
    skills: parseDelimitedList(form.skillsText),
    experiences: form.experiences.map(toExperiencePayload).filter((entry): entry is ProfileExperience => entry !== null),
    projects: form.projects.map(toProjectPayload).filter((entry): entry is ProfileProject => entry !== null),
    education: form.education.map(toEducationPayload).filter((entry): entry is ProfileEducation => entry !== null),
  };
}

function readStringArrayField(name: string, value: unknown): string[] | undefined {
  if (value === undefined) return undefined;
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string')) {
    throw new Error(`${name} must be an array of strings.`);
  }
  return value.map((item) => item.trim()).filter(Boolean);
}

function readObjectArrayField(name: string, value: unknown): Array<Record<string, unknown>> | undefined {
  if (value === undefined) return undefined;
  if (!Array.isArray(value) || value.some((item) => !item || typeof item !== 'object' || Array.isArray(item))) {
    throw new Error(`${name} must be a JSON array of objects.`);
  }
  return value as Array<Record<string, unknown>>;
}

function parseProfileJsonPatch(text: string): Partial<UpsertUserProfileRequest> {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error('Advanced JSON must be valid JSON.');
  }

  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('Advanced JSON must be an object.');
  }

  const payload = parsed as Record<string, unknown>;
  const patch: Partial<UpsertUserProfileRequest> = {};

  if (payload.id !== undefined) {
    if (typeof payload.id !== 'string') throw new Error('id must be a string.');
    patch.id = payload.id.trim() || 'primary';
  }

  if (payload.full_name !== undefined) {
    if (typeof payload.full_name !== 'string') throw new Error('full_name must be a string.');
    patch.full_name = payload.full_name;
  }

  if (payload.headline !== undefined) {
    if (payload.headline !== null && typeof payload.headline !== 'string') throw new Error('headline must be a string or null.');
    patch.headline = payload.headline as string | null;
  }

  if (payload.summary !== undefined) {
    if (payload.summary !== null && typeof payload.summary !== 'string') throw new Error('summary must be a string or null.');
    patch.summary = payload.summary as string | null;
  }

  const skills = readStringArrayField('skills', payload.skills);
  if (skills !== undefined) patch.skills = skills;

  const experiences = readObjectArrayField('experiences', payload.experiences);
  if (experiences !== undefined) patch.experiences = experiences;

  const projects = readObjectArrayField('projects', payload.projects);
  if (projects !== undefined) patch.projects = projects;

  const education = readObjectArrayField('education', payload.education);
  if (education !== undefined) patch.education = education;

  return patch;
}

function mergeFormWithPatch(current: ProfileFormState, patch: Partial<UpsertUserProfileRequest>): ProfileFormState {
  const mergedProfile: Partial<UserProfile> = {
    id: patch.id ?? current.id,
    full_name: patch.full_name ?? current.fullName,
    headline: patch.headline ?? current.headline,
    summary: patch.summary ?? current.summary,
    skills: patch.skills ?? parseDelimitedList(current.skillsText),
    experiences: patch.experiences ?? current.experiences.map(toExperiencePayload).filter((entry): entry is ProfileExperience => entry !== null),
    projects: patch.projects ?? current.projects.map(toProjectPayload).filter((entry): entry is ProfileProject => entry !== null),
    education: patch.education ?? current.education.map(toEducationPayload).filter((entry): entry is ProfileEducation => entry !== null),
  };
  return toFormState(mergedProfile);
}

export function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [profileSignal, setProfileSignal] = useState<'loading' | 'ready' | 'missing' | 'error'>('loading');
  const [form, setForm] = useState<ProfileFormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [advancedJsonDraft, setAdvancedJsonDraft] = useState('');
  const [advancedJsonError, setAdvancedJsonError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    getUserProfile()
      .then((profile) => {
        if (!active) return;
        setForm(toFormState(profile));
        setProfileSignal('ready');
      })
      .catch((err: unknown) => {
        if (!active) return;
        if (err instanceof ApiError && err.status === 404) {
          setNotice('No profile saved yet. Fill this form and click Save Profile.');
          setProfileSignal('missing');
          return;
        }
        setLoadError(err instanceof Error ? err.message : 'Unable to load profile.');
        setProfileSignal('error');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const canonicalJson = useMemo(() => JSON.stringify(toProfilePayload(form), null, 2), [form]);

  useEffect(() => {
    setAdvancedJsonDraft(canonicalJson);
    setAdvancedJsonError(null);
  }, [canonicalJson]);

  function updateForm<K extends keyof ProfileFormState>(key: K, value: ProfileFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateExperience(index: number, key: keyof ExperienceFormState, value: string) {
    setForm((current) => {
      const next = [...current.experiences];
      next[index] = { ...next[index], [key]: value };
      return { ...current, experiences: next };
    });
  }

  function updateProject(index: number, key: keyof ProjectFormState, value: string) {
    setForm((current) => {
      const next = [...current.projects];
      next[index] = { ...next[index], [key]: value };
      return { ...current, projects: next };
    });
  }

  function updateEducation(index: number, key: keyof EducationFormState, value: string) {
    setForm((current) => {
      const next = [...current.education];
      next[index] = { ...next[index], [key]: value };
      return { ...current, education: next };
    });
  }

  function addExperience() {
    setForm((current) => ({ ...current, experiences: [...current.experiences, emptyExperience()] }));
  }

  function addProject() {
    setForm((current) => ({ ...current, projects: [...current.projects, emptyProject()] }));
  }

  function addEducation() {
    setForm((current) => ({ ...current, education: [...current.education, emptyEducation()] }));
  }

  function removeExperience(index: number) {
    setForm((current) => ({
      ...current,
      experiences: ensureAtLeastOne(
        current.experiences.filter((_, idx) => idx !== index),
        emptyExperience,
      ),
    }));
  }

  function removeProject(index: number) {
    setForm((current) => ({
      ...current,
      projects: ensureAtLeastOne(
        current.projects.filter((_, idx) => idx !== index),
        emptyProject,
      ),
    }));
  }

  function removeEducation(index: number) {
    setForm((current) => ({
      ...current,
      education: ensureAtLeastOne(
        current.education.filter((_, idx) => idx !== index),
        emptyEducation,
      ),
    }));
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setSubmitError(null);
    setNotice(null);

    try {
      const profile = await upsertUserProfile(toProfilePayload(form));

      setForm(toFormState(profile));
      setNotice('Profile saved. Resume generation can now use this data.');
      setProfileSignal('ready');
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : 'Unable to save profile.');
    } finally {
      setSaving(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    setResumeFile(file ?? null);
    setUploadError(null);
  }

  async function handleResumeUpload() {
    if (!resumeFile) return;
    setUploading(true);
    setUploadError(null);
    setNotice(null);

    try {
      const result = await uploadResumeToProfile(resumeFile);
      setForm((current) => mergeFormWithPatch(current, result.profile));
      if (result.warnings.length > 0) {
        setNotice(`Resume parsed with warnings: ${result.warnings.join(' | ')}`);
      } else {
        setNotice('Resume parsed. Review structured fields and click Save Profile to persist.');
      }
      setProfileSignal('ready');
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : 'Unable to parse uploaded resume.');
    } finally {
      setUploading(false);
    }
  }

  function handleApplyAdvancedJson() {
    setAdvancedJsonError(null);
    try {
      const patch = parseProfileJsonPatch(advancedJsonDraft);
      setForm((current) => mergeFormWithPatch(current, patch));
      setNotice('Advanced JSON applied to structured editor. Click Save Profile to persist.');
    } catch (err: unknown) {
      setAdvancedJsonError(err instanceof Error ? err.message : 'Unable to apply advanced JSON.');
    }
  }

  return (
    <Layout
      title="Profile Builder"
      subtitle="Store your resume source data: identity, summary, skills, and structured history."
    >
      <DiagnosticsPanel profileSignal={profileSignal} />
      <AsyncBlock loading={loading} error={loadError} loadingLabel="Loading profile...">
        <section className="panel">
          <h2>Resume Upload</h2>
          <p className="muted">
            Upload a <code>.pdf</code> or <code>.docx</code> resume and map parsed output into the structured profile editor.
          </p>
          <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={handleFileChange} aria-label="Resume file upload" />
          {resumeFile ? <p className="tiny muted">Selected: {resumeFile.name}</p> : null}
          <div className="actions-row">
            <button type="button" onClick={handleResumeUpload} disabled={!resumeFile || uploading}>
              {uploading ? 'Parsing...' : 'Parse Resume to Form'}
            </button>
          </div>
          {uploadError ? <p className="error">{uploadError}</p> : null}
        </section>

        <section className="panel">
          <h2>Candidate Profile</h2>
          <p className="muted">
            Structured editing is the primary path for profile quality and reviewability. <code>full_name</code> is required.
          </p>

          <form className="form-grid" onSubmit={handleSave}>
            <div className="section-stack">
              <h3>Identity</h3>
              <div className="split-grid">
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
              </div>

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
            </div>

            <div className="section-stack">
              <h3>Skills</h3>
              <label>
                <span>Skills (newline or comma separated)</span>
                <textarea
                  value={form.skillsText}
                  onChange={(event) => updateForm('skillsText', event.target.value)}
                  placeholder={'Python\nFastAPI\nSQL'}
                />
              </label>
            </div>

            <div className="section-stack">
              <div className="actions-row">
                <h3>Experience</h3>
                <button type="button" onClick={addExperience}>
                  Add Experience
                </button>
              </div>
              <div className="entry-list">
                {form.experiences.map((experience, index) => (
                  <div key={`exp-${index}`} className="entry-card">
                    <div className="actions-row">
                      <strong>Experience {index + 1}</strong>
                      <button type="button" onClick={() => removeExperience(index)}>
                        Remove
                      </button>
                    </div>
                    <div className="split-grid">
                      <label>
                        <span>Experience ID</span>
                        <input
                          value={experience.id}
                          onChange={(event) => updateExperience(index, 'id', event.target.value)}
                          aria-label={`Experience ID ${index + 1}`}
                        />
                      </label>
                      <label>
                        <span>Company</span>
                        <input
                          value={experience.company}
                          onChange={(event) => updateExperience(index, 'company', event.target.value)}
                          aria-label={`Company ${index + 1}`}
                        />
                      </label>
                    </div>
                    <div className="split-grid">
                      <label>
                        <span>Title</span>
                        <input
                          value={experience.title}
                          onChange={(event) => updateExperience(index, 'title', event.target.value)}
                          aria-label={`Title ${index + 1}`}
                        />
                      </label>
                      <label>
                        <span>Start Date</span>
                        <input
                          value={experience.startDate}
                          onChange={(event) => updateExperience(index, 'startDate', event.target.value)}
                          placeholder="2024-01-01"
                          aria-label={`Start Date ${index + 1}`}
                        />
                      </label>
                    </div>
                    <div className="split-grid">
                      <label>
                        <span>End Date</span>
                        <input
                          value={experience.endDate}
                          onChange={(event) => updateExperience(index, 'endDate', event.target.value)}
                          placeholder="Leave blank if current"
                          aria-label={`End Date ${index + 1}`}
                        />
                      </label>
                      <label>
                        <span>Related Skills</span>
                        <input
                          value={experience.skillsText}
                          onChange={(event) => updateExperience(index, 'skillsText', event.target.value)}
                          placeholder="Python, SQL, React"
                          aria-label={`Experience Skills ${index + 1}`}
                        />
                      </label>
                    </div>
                    <label>
                      <span>Bullets (newline separated)</span>
                      <textarea
                        value={experience.bulletsText}
                        onChange={(event) => updateExperience(index, 'bulletsText', event.target.value)}
                        aria-label={`Experience Bullets ${index + 1}`}
                      />
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="section-stack">
              <div className="actions-row">
                <h3>Projects</h3>
                <button type="button" onClick={addProject}>
                  Add Project
                </button>
              </div>
              <div className="entry-list">
                {form.projects.map((project, index) => (
                  <div key={`project-${index}`} className="entry-card">
                    <div className="actions-row">
                      <strong>Project {index + 1}</strong>
                      <button type="button" onClick={() => removeProject(index)}>
                        Remove
                      </button>
                    </div>
                    <div className="split-grid">
                      <label>
                        <span>Project ID</span>
                        <input
                          value={project.id}
                          onChange={(event) => updateProject(index, 'id', event.target.value)}
                          aria-label={`Project ID ${index + 1}`}
                        />
                      </label>
                      <label>
                        <span>Name</span>
                        <input
                          value={project.name}
                          onChange={(event) => updateProject(index, 'name', event.target.value)}
                          aria-label={`Project Name ${index + 1}`}
                        />
                      </label>
                    </div>
                    <label>
                      <span>Description</span>
                      <textarea
                        value={project.description}
                        onChange={(event) => updateProject(index, 'description', event.target.value)}
                        aria-label={`Project Description ${index + 1}`}
                      />
                    </label>
                    <div className="split-grid">
                      <label>
                        <span>Skills</span>
                        <input
                          value={project.skillsText}
                          onChange={(event) => updateProject(index, 'skillsText', event.target.value)}
                          placeholder="TypeScript, Vite"
                          aria-label={`Project Skills ${index + 1}`}
                        />
                      </label>
                      <label>
                        <span>URL</span>
                        <input
                          value={project.url}
                          onChange={(event) => updateProject(index, 'url', event.target.value)}
                          placeholder="https://example.com"
                          aria-label={`Project URL ${index + 1}`}
                        />
                      </label>
                    </div>
                    <label>
                      <span>Bullets (newline separated)</span>
                      <textarea
                        value={project.bulletsText}
                        onChange={(event) => updateProject(index, 'bulletsText', event.target.value)}
                        aria-label={`Project Bullets ${index + 1}`}
                      />
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="section-stack">
              <div className="actions-row">
                <h3>Education</h3>
                <button type="button" onClick={addEducation}>
                  Add Education
                </button>
              </div>
              <div className="entry-list">
                {form.education.map((education, index) => (
                  <div key={`education-${index}`} className="entry-card">
                    <div className="actions-row">
                      <strong>Education {index + 1}</strong>
                      <button type="button" onClick={() => removeEducation(index)}>
                        Remove
                      </button>
                    </div>
                    <div className="split-grid">
                      <label>
                        <span>Education ID</span>
                        <input
                          value={education.id}
                          onChange={(event) => updateEducation(index, 'id', event.target.value)}
                          aria-label={`Education ID ${index + 1}`}
                        />
                      </label>
                      <label>
                        <span>School</span>
                        <input
                          value={education.school}
                          onChange={(event) => updateEducation(index, 'school', event.target.value)}
                          aria-label={`School ${index + 1}`}
                        />
                      </label>
                    </div>
                    <div className="split-grid">
                      <label>
                        <span>Degree</span>
                        <input
                          value={education.degree}
                          onChange={(event) => updateEducation(index, 'degree', event.target.value)}
                          aria-label={`Degree ${index + 1}`}
                        />
                      </label>
                      <label>
                        <span>Field</span>
                        <input
                          value={education.field}
                          onChange={(event) => updateEducation(index, 'field', event.target.value)}
                          aria-label={`Field ${index + 1}`}
                        />
                      </label>
                    </div>
                    <div className="split-grid">
                      <label>
                        <span>Start Date</span>
                        <input
                          value={education.startDate}
                          onChange={(event) => updateEducation(index, 'startDate', event.target.value)}
                          placeholder="2020-09-01"
                          aria-label={`Education Start Date ${index + 1}`}
                        />
                      </label>
                      <label>
                        <span>End Date</span>
                        <input
                          value={education.endDate}
                          onChange={(event) => updateEducation(index, 'endDate', event.target.value)}
                          placeholder="2024-05-01"
                          aria-label={`Education End Date ${index + 1}`}
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="actions-row">
              <button type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save Profile'}
              </button>
            </div>
          </form>

          <details className="advanced-panel">
            <summary>Advanced: Raw JSON Fallback</summary>
            <p className="tiny muted">
              Use only when needed. Structured editor remains the default and recommended profile workflow.
            </p>
            <label>
              <span>Profile JSON</span>
              <textarea
                value={advancedJsonDraft}
                onChange={(event) => setAdvancedJsonDraft(event.target.value)}
                aria-label="Profile JSON"
              />
            </label>
            <div className="actions-row">
              <button type="button" onClick={() => setAdvancedJsonDraft(canonicalJson)}>
                Reset to Current Form
              </button>
              <button type="button" onClick={handleApplyAdvancedJson}>
                Apply JSON to Form
              </button>
            </div>
            {advancedJsonError ? <p className="error">{advancedJsonError}</p> : null}
          </details>

          {notice ? <p className="notice">{notice}</p> : null}
          {submitError ? <p className="error">{submitError}</p> : null}
        </section>
      </AsyncBlock>
    </Layout>
  );
}
