import {
  ApplicationDetail,
  ApplicationSummary,
  ApplicationStatus,
  PaginatedResponse,
  ResumeIngestResult,
  ResumeTimelineEntry,
  ResumeVersionDetail,
  UpsertUserProfileRequest,
  UserProfile,
} from '../types';

const API_BASE = '/api/v1';
const PROFILE_INGEST_PATH = (import.meta.env.VITE_PROFILE_INGEST_PATH as string | undefined) ?? '/profile/ingest';

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

  const response = await fetch(`${API_BASE}${path}`, {
    headers,
    ...init,
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

export async function uploadResumeToProfile(file: File): Promise<ResumeIngestResult> {
  const formData = new FormData();
  formData.append('resume', file);

  const payload = await request<unknown>(PROFILE_INGEST_PATH, {
    method: 'POST',
    body: formData,
  });

  const envelope = asObject(payload);
  const draft =
    toProfileDraft(envelope?.profile) ??
    toProfileDraft(envelope?.parsed_profile) ??
    toProfileDraft(payload);

  if (!draft) {
    throw new ApiError(
      502,
      'Resume upload succeeded but the response did not include a usable profile payload from the S4-A contract.',
      payload,
    );
  }

  const warnings = readStringArray(envelope?.warnings);
  return { profile: draft, warnings };
}
