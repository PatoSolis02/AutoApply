import {
  AuditExportPayload,
  ApplicationDetail,
  ApplicationSummary,
  ApplicationStatus,
  CaptureJobRequest,
  CaptureJobResponse,
  GenerateResumeVersionResponse,
  PaginatedResponse,
  ResumeIngestResult,
  ResumeTimelineEntry,
  ResumeVersionDetail,
  UpsertUserProfileRequest,
  UserProfile,
} from '../types';

const API_BASE = '/api/v1';
const PROFILE_PARSE_PATH = (import.meta.env.VITE_PROFILE_INGEST_PATH as string | undefined) ?? '/profile/resume-parse';
const PROFILE_PARSE_LEGACY_PATH = '/profile/ingest';
const CAPTURE_PATH = '/jobs/capture';
const CAPTURE_LEGACY_PATH = '/capture';

export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, message: string, payload: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

export function errorMessageForStatus(status: number): string {
  if (status === 409) {
    return 'This status change conflicts with the allowed application lifecycle. Refresh and choose a valid transition.';
  }

  if (status === 422) {
    return 'This action is blocked by compliance checks. Review claims and approval requirements before trying again.';
  }

  return 'Something went wrong while saving. Please retry.';
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(resolveApiPath(path), {
    ...init,
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let data: unknown;
  if (text) {
    try {
      data = JSON.parse(text) as unknown;
    } catch {
      const isLikelyHtml = text.trimStart().startsWith('<');
      const detail = isLikelyHtml
        ? 'Received HTML instead of JSON from the API. Ensure backend is running on 127.0.0.1:8000 and Vite proxy is active.'
        : 'Received a non-JSON API response.';
      throw new ApiError(response.status, detail, {
        contentType: response.headers.get('content-type'),
      });
    }
  }

  if (!response.ok) {
    const message =
      typeof data === 'object' && data !== null && 'detail' in data
        ? String((data as { detail?: unknown }).detail)
        : errorMessageForStatus(response.status);

    throw new ApiError(response.status, message, data);
  }

  return data as T;
}

function asObject(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}

function resolveApiPath(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  const normalized = path.startsWith('/') ? path : `/${path}`;
  if (normalized.startsWith('/api/')) {
    return normalized;
  }
  return `${API_BASE}${normalized}`;
}

function dedupePaths(paths: string[]): string[] {
  const unique = new Set<string>();
  for (const path of paths) {
    const trimmed = path.trim();
    if (!trimmed) continue;
    unique.add(trimmed.startsWith('/') || trimmed.startsWith('http') ? trimmed : `/${trimmed}`);
  }
  return [...unique];
}

function envelopeCandidates(payload: unknown): Record<string, unknown>[] {
  const root = asObject(payload);
  if (!root) return [];

  const candidates: Record<string, unknown>[] = [root];
  const nestedKeys = ['data', 'result', 'response', 'payload'];
  for (const key of nestedKeys) {
    const nested = asObject(root[key]);
    if (nested) {
      candidates.push(nested);
    }
  }
  return candidates;
}

function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean);
}

function readObjectArray(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) return [];
  return value.filter((item) => item && typeof item === 'object' && !Array.isArray(item)) as Array<Record<string, unknown>>;
}

function readNullableString(value: unknown): string | null | undefined {
  if (value === null || value === undefined) return value as null | undefined;
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  }
  return undefined;
}

function readNonEmptyString(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined;
  const trimmed = value.trim();
  return trimmed || undefined;
}

function readIdFromObject(value: unknown): string | undefined {
  const source = asObject(value);
  if (!source) return undefined;
  return readNonEmptyString(source.id) ?? readNonEmptyString(source.uuid);
}

function readWarningsFromEnvelope(envelope: Record<string, unknown> | null): string[] {
  if (!envelope) return [];
  return readStringArray(envelope.warnings ?? envelope.warning_messages ?? envelope.warningMessages);
}

function toProfileDraft(value: unknown): UpsertUserProfileRequest | null {
  const source = asObject(value);
  if (!source) return null;

  const fullNameRaw = source.full_name;
  const fullName = typeof fullNameRaw === 'string' ? fullNameRaw.trim() : '';
  if (!fullName) return null;

  const idRaw = source.id;
  const id = typeof idRaw === 'string' && idRaw.trim() ? idRaw.trim() : undefined;

  return {
    id,
    full_name: fullName,
    headline: readNullableString(source.headline),
    summary: readNullableString(source.summary),
    skills: readStringArray(source.skills),
    experiences: readObjectArray(source.experiences),
    projects: readObjectArray(source.projects),
    education: readObjectArray(source.education),
  };
}

function normalizeCollection<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) {
    return payload as T[];
  }

  if (payload && typeof payload === 'object') {
    const typed = payload as {
      items?: unknown;
      data?: unknown;
      results?: unknown;
    };

    if (Array.isArray(typed.items)) return typed.items as T[];
    if (Array.isArray(typed.data)) return typed.data as T[];
    if (Array.isArray(typed.results)) return typed.results as T[];
  }

  return [];
}

export async function getApplications(): Promise<PaginatedResponse<ApplicationSummary>> {
  const payload = await request<unknown>('/applications');

  return {
    items: normalizeCollection<ApplicationSummary>(payload),
    ...(typeof payload === 'object' && payload !== null ? payload : {}),
  };
}

export async function getApplicationDetail(applicationId: string): Promise<ApplicationDetail> {
  const payload = await request<unknown>(`/applications/${applicationId}`);

  if (payload && typeof payload === 'object' && 'application' in payload) {
    const wrapped = payload as { application: ApplicationDetail };
    return wrapped.application;
  }

  return payload as ApplicationDetail;
}

export async function patchApplicationStatus(
  applicationId: string,
  targetStatus: ApplicationStatus,
): Promise<ApplicationDetail> {
  const payload = await request<unknown>(`/applications/${applicationId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ target_status: targetStatus }),
  });

  if (payload && typeof payload === 'object' && 'application' in payload) {
    const wrapped = payload as { application: ApplicationDetail };
    return wrapped.application;
  }

  return payload as ApplicationDetail;
}

export async function getResumeTimeline(applicationId: string): Promise<ResumeTimelineEntry[]> {
  const payload = await request<unknown>(`/applications/${applicationId}/resume-versions`);
  return normalizeCollection<ResumeTimelineEntry>(payload);
}

export async function captureJob(payload: CaptureJobRequest): Promise<CaptureJobResponse> {
  const capturePaths = dedupePaths([CAPTURE_PATH, CAPTURE_LEGACY_PATH]);
  let rawPayload: unknown = null;
  let lastError: unknown;

  for (const path of capturePaths) {
    try {
      rawPayload = await request<unknown>(path, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      break;
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404 || path === capturePaths[capturePaths.length - 1]) {
        throw error;
      }
      lastError = error;
    }
  }

  if (rawPayload === null) {
    if (lastError instanceof ApiError) throw lastError;
    throw new ApiError(502, 'Capture request did not return a response payload.', lastError ?? null);
  }

  for (const envelope of envelopeCandidates(rawPayload)) {
    const applicationId =
      readNonEmptyString(envelope.application_id) ??
      readNonEmptyString(envelope.applicationId) ??
      readIdFromObject(envelope.application);
    const jobPostingId =
      readNonEmptyString(envelope.job_posting_id) ??
      readNonEmptyString(envelope.jobPostingId) ??
      readIdFromObject(envelope.job_posting) ??
      readIdFromObject(envelope.jobPosting);
    if (applicationId && jobPostingId) {
      return {
        application_id: applicationId,
        job_posting_id: jobPostingId,
      };
    }
  }

  throw new ApiError(
    502,
    'Capture succeeded but response did not include application_id and job_posting_id in a supported envelope.',
    rawPayload,
  );
}

export async function generateResumeVersion(
  applicationId: string,
  templateId: string,
): Promise<GenerateResumeVersionResponse> {
  const rawPayload = await request<unknown>(`/applications/${applicationId}/resume-versions/generate`, {
    method: 'POST',
    body: JSON.stringify({ template_id: templateId }),
  });

  for (const envelope of envelopeCandidates(rawPayload)) {
    const resumeVersionId =
      readNonEmptyString(envelope.resume_version_id) ??
      readNonEmptyString(envelope.resumeVersionId) ??
      readIdFromObject(envelope.resume_version) ??
      readIdFromObject(envelope.resumeVersion);
    if (!resumeVersionId) continue;

    return {
      resume_version_id: resumeVersionId,
      warnings: readStringArray(envelope.warnings ?? envelope.warning_messages ?? envelope.warningMessages),
      blocked_reasons: readStringArray(envelope.blocked_reasons ?? envelope.blockedReasons),
    };
  }

  throw new ApiError(
    502,
    'Resume generation succeeded but response did not include resume_version_id in a supported envelope.',
    rawPayload,
  );
}

export async function getResumeVersion(resumeVersionId: string): Promise<ResumeVersionDetail> {
  return request<ResumeVersionDetail>(`/resume-versions/${resumeVersionId}`);
}

export async function approveResumeVersion(resumeVersionId: string): Promise<ResumeVersionDetail> {
  return request<ResumeVersionDetail>(`/resume-versions/${resumeVersionId}/approve`, {
    method: 'POST',
  });
}

export async function getUserProfile(): Promise<UserProfile> {
  return request<UserProfile>('/profile');
}

export async function upsertUserProfile(payload: UpsertUserProfileRequest): Promise<UserProfile> {
  return request<UserProfile>('/profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

async function parseResumeUpload(path: string, file: File): Promise<unknown> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('resume', file);
  return request<unknown>(path, {
    method: 'POST',
    body: formData,
  });
}

export async function uploadResumeToProfile(file: File): Promise<ResumeIngestResult> {
  const parseEndpoints = dedupePaths([
    PROFILE_PARSE_PATH,
    '/profile/resume-parse',
    PROFILE_PARSE_LEGACY_PATH,
    '/profile/ingest',
    '/api/v1/profile/resume-parse',
    '/api/v1/profile/ingest',
  ]);

  let payload: unknown = null;
  let lastError: unknown;
  for (const path of parseEndpoints) {
    try {
      payload = await parseResumeUpload(path, file);
      break;
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404 || path === parseEndpoints[parseEndpoints.length - 1]) {
        throw error;
      }
      lastError = error;
    }
  }

  if (payload === null) {
    if (lastError instanceof ApiError) throw lastError;
    throw new ApiError(502, 'Resume parse request did not return a response payload.', lastError ?? null);
  }

  let draft: UpsertUserProfileRequest | null = null;
  let warnings: string[] = [];
  for (const envelope of envelopeCandidates(payload)) {
    draft =
      toProfileDraft(envelope.profile) ??
      toProfileDraft(envelope.parsed_profile) ??
      toProfileDraft(envelope.parsedProfile) ??
      toProfileDraft(envelope.resume_profile) ??
      toProfileDraft(envelope.resumeProfile) ??
      toProfileDraft(envelope);
    if (draft) {
      warnings = readWarningsFromEnvelope(envelope);
      break;
    }
  }

  if (!draft) {
    throw new ApiError(
      502,
      'Resume upload succeeded but response did not include a supported profile envelope (profile, parsed_profile, or direct profile object).',
      payload,
    );
  }

  return { profile: draft, warnings };
}

export async function getApplicationAuditExport(applicationId: string): Promise<AuditExportPayload> {
  return request<AuditExportPayload>(`/applications/${applicationId}/audit-export`);
}
