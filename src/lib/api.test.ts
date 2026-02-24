import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  captureJob,
  errorMessageForStatus,
  generateResumeVersion,
  uploadResumeToProfile,
} from './api';

const fetchMock = vi.fn<typeof fetch>();

describe('api contract fallback handling', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('normalizes capture response from nested envelope variants', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          data: {
            application: { id: 'app-1' },
            job_posting: { id: 'job-1' },
          },
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    const result = await captureJob({
      title: 'Backend Engineer',
      company: 'Acme',
      location: 'Rochester, NY',
      job_url: 'https://www.linkedin.com/jobs/view/123',
      description_raw: 'Build reliable APIs',
      captured_at: '2026-02-24T10:00:00Z',
    });

    expect(result).toEqual({
      application_id: 'app-1',
      job_posting_id: 'job-1',
    });
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/jobs/capture',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('falls back to legacy capture endpoint after canonical 404', async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'not found' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            application_id: 'app-2',
            job_posting_id: 'job-2',
          }),
          {
            status: 201,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      );

    const result = await captureJob({
      title: 'Backend Engineer',
      company: 'Acme',
      location: null,
      job_url: 'https://www.linkedin.com/jobs/view/456',
      description_raw: 'Build services',
      captured_at: '2026-02-24T10:00:00Z',
    });

    expect(result.application_id).toBe('app-2');
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/jobs/capture');
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/capture');
  });

  it('surfaces contract mismatch when capture ids are missing', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          data: { application: { id: 'app-only' } },
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(
      captureJob({
        title: 'Backend Engineer',
        company: 'Acme',
        location: null,
        job_url: 'https://www.linkedin.com/jobs/view/456',
        description_raw: 'Build services',
        captured_at: '2026-02-24T10:00:00Z',
      }),
    ).rejects.toMatchObject({
      status: 502,
      message: expect.stringContaining('application_id and job_posting_id'),
    });
  });

  it('normalizes generate response from nested envelope variants', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          result: {
            resumeVersion: { id: 'ver-1' },
            warningMessages: ['minor'],
            blockedReasons: ['missing-proof'],
          },
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    const result = await generateResumeVersion('app-1', 'default');

    expect(result).toEqual({
      resume_version_id: 'ver-1',
      warnings: ['minor'],
      blocked_reasons: ['missing-proof'],
    });
  });

  it('falls back across resume parse endpoint variants on 404', async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'not found' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            result: {
              parsed_profile: {
                id: 'primary',
                full_name: 'Taylor Dev',
                skills: ['Python'],
                experiences: [],
                projects: [],
                education: [],
              },
              warning_messages: ['normalized dates'],
            },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      );

    const result = await uploadResumeToProfile(new File(['resume'], 'resume.pdf', { type: 'application/pdf' }));

    expect(result.profile.full_name).toBe('Taylor Dev');
    expect(result.warnings).toEqual(['normalized dates']);
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/profile/resume-parse');
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/profile/ingest');
  });

  it('returns explicit mismatch errors when resume upload response has no profile envelope', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ result: { warnings: ['ok'] } }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(uploadResumeToProfile(new File(['resume'], 'resume.pdf', { type: 'application/pdf' }))).rejects.toMatchObject({
      status: 502,
      message: expect.stringContaining('supported profile envelope'),
    });
  });
});

describe('api error message mapping', () => {
  it('maps 409 to transition conflict message', () => {
    expect(errorMessageForStatus(409)).toContain('allowed application lifecycle');
  });

  it('maps 422 to compliance block message', () => {
    expect(errorMessageForStatus(422)).toContain('blocked by compliance checks');
  });

  it('falls back for other statuses', () => {
    expect(errorMessageForStatus(500)).toContain('Something went wrong');
  });
});
