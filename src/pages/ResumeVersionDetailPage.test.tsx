import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ResumeVersionDetailPage } from './ResumeVersionDetailPage';
import * as api from '../lib/api';
import { ResumeVersionDetail } from '../types';

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api');
  return {
    ...actual,
    getResumeVersion: vi.fn(),
    approveResumeVersion: vi.fn(),
  };
});

const getResumeVersionMock = vi.mocked(api.getResumeVersion);

function renderPage() {
  render(
    <MemoryRouter initialEntries={['/applications/app-1/resume-versions/ver-1']}>
      <Routes>
        <Route path="/applications/:applicationId/resume-versions/:resumeVersionId" element={<ResumeVersionDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ResumeVersionDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    const detail: ResumeVersionDetail = {
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
      render_model_json: {
        headline: 'Platform Engineer',
        summary: 'Build APIs',
        selected_experience_ids: ['exp-1'],
        selected_project_ids: [],
        selected_skill_keywords: ['python'],
        sections: {
          experience: [
            {
              entry_id: 'exp-1',
              bullets: [{ id: 'b-1', text: 'Built APIs' }],
            },
          ],
          projects: [],
        },
      },
      change_log: {
        added: ['Built APIs'],
        removed: ['Old bullet'],
        reworded: [
          {
            from: 'Created backend',
            to: 'Built production backend',
            reason: 'clarity',
          },
        ],
      },
      claims_map: [
        {
          bullet_id: 'b-2',
          bullet_text: 'Led SRE team',
          source_type: 'experience',
          source_id: 'exp-2',
          evidence_text: 'No matching evidence',
          verification_status: 'rejected',
        },
        {
          bullet_id: 'b-1',
          bullet_text: 'Built APIs',
          source_type: 'experience',
          source_id: 'exp-1',
          evidence_text: 'Built APIs',
          verification_status: 'supported',
        },
      ],
    };

    getResumeVersionMock.mockResolvedValue(detail);
  });

  it('renders change-log and claim summaries with rejected claims emphasized', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Version Metadata')).toBeInTheDocument();
    });

    expect(screen.getByText(/Total changes tracked: 3/)).toBeInTheDocument();
    expect(screen.getByText(/supported=1 \| rejected=1/)).toBeInTheDocument();
    expect(screen.getByText('b-2').closest('article')).toHaveClass('claim-card-danger');
    expect(screen.getByText('b-1').closest('article')).toHaveClass('claim-card');
  });
});
