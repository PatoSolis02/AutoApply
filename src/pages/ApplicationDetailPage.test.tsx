import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApplicationDetailPage } from './ApplicationDetailPage';
import * as api from '../lib/api';
import { ApplicationDetail, ResumeTimelineEntry } from '../types';

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api');
  return {
    ...actual,
    getApplicationDetail: vi.fn(),
    getResumeTimeline: vi.fn(),
    patchApplicationStatus: vi.fn(),
    generateResumeVersion: vi.fn(),
    getApplicationAuditExport: vi.fn(),
  };
});

const getApplicationDetailMock = vi.mocked(api.getApplicationDetail);
const getResumeTimelineMock = vi.mocked(api.getResumeTimeline);
const patchApplicationStatusMock = vi.mocked(api.patchApplicationStatus);
const generateResumeVersionMock = vi.mocked(api.generateResumeVersion);
const getApplicationAuditExportMock = vi.mocked(api.getApplicationAuditExport);

const baseApplication: Omit<ApplicationDetail, 'status' | 'latest_resume_version'> = {
  id: 'app-1',
  company: 'Acme',
  role_title: 'Platform Engineer',
  job_url: 'https://example.com/jobs/1',
  job_source: 'linkedin',
  location: 'Rochester, NY',
  notes: '',
  fit_score: null,
  created_at: '2026-02-23T12:00:00Z',
  updated_at: '2026-02-23T12:00:00Z',
};

const timelineEntry: ResumeTimelineEntry = {
  id: 'ver-1',
  application_id: 'app-1',
  template_id: 'modern',
  pdf_path: 'artifacts/resumes/app-1/ver-1.pdf',
  rendered_html_path: 'artifacts/resumes/app-1/ver-1.html',
  approval: {
    approved: false,
    approved_at: null,
  },
  created_at: '2026-02-23T12:30:00Z',
};

function renderPage() {
  render(
    <MemoryRouter initialEntries={['/applications/app-1']}>
      <Routes>
        <Route path="/applications/:applicationId" element={<ApplicationDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ApplicationDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    const captured: ApplicationDetail = {
      ...baseApplication,
      status: 'captured',
      latest_resume_version: null,
    };
    const drafting: ApplicationDetail = {
      ...baseApplication,
      status: 'drafting',
      latest_resume_version: null,
    };
    const withVersion: ApplicationDetail = {
      ...baseApplication,
      status: 'drafting',
      latest_resume_version: timelineEntry,
    };

    getApplicationDetailMock.mockResolvedValueOnce(captured).mockResolvedValueOnce(withVersion);
    getResumeTimelineMock.mockResolvedValueOnce([]).mockResolvedValueOnce([timelineEntry]);
    patchApplicationStatusMock.mockResolvedValueOnce(drafting);
    generateResumeVersionMock.mockResolvedValueOnce({
      resume_version_id: 'ver-1',
      warnings: [],
      blocked_reasons: [],
    });
    getApplicationAuditExportMock.mockResolvedValue({
      application: withVersion,
      job_posting: {
        id: 'job-1',
        application_id: 'app-1',
        raw_text: 'Build APIs',
        structured_json: { keywords: ['python'] },
        captured_at: '2026-02-23T12:00:00Z',
      },
      resume_versions: [
        {
          ...timelineEntry,
          render_model_json: {
            headline: 'Platform Engineer',
            summary: 'Build APIs',
            selected_experience_ids: [],
            selected_project_ids: [],
            selected_skill_keywords: [],
            sections: { experience: [], projects: [] },
          },
          change_log: { added: [], removed: [], reworded: [] },
          claims_map: [],
        },
      ],
      generated_at: '2026-02-23T12:31:00Z',
    });
  });

  it('runs generate flow and exposes audit export', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Platform Engineer')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Generate Resume' }));

    await waitFor(() => {
      expect(patchApplicationStatusMock).toHaveBeenCalledWith('app-1', 'drafting');
    });
    await waitFor(() => {
      expect(generateResumeVersionMock).toHaveBeenCalledWith('app-1', 'modern');
    });
    await waitFor(() => {
      expect(screen.getByText(/resume version ver-1 generated/i)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'View detail' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'View Audit Export' }));
    await waitFor(() => {
      expect(getApplicationAuditExportMock).toHaveBeenCalledWith('app-1');
    });
    await waitFor(() => {
      expect(screen.getByText(/Generated/)).toBeInTheDocument();
    });
    expect(screen.getByRole('link', { name: 'Download JSON' })).toBeInTheDocument();
  });
});
