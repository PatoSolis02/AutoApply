import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { StatusEditor } from './StatusEditor';
import * as api from '../lib/api';

const baseApplication = {
  id: 'app-1',
  company: 'Acme',
  role_title: 'Software Engineer',
  job_url: 'https://example.com/job',
  job_source: 'linkedin' as const,
  location: 'Remote',
  status: 'captured' as const,
  notes: '',
  fit_score: null,
  created_at: '2026-02-20T10:00:00Z',
  updated_at: '2026-02-20T10:00:00Z',
  latest_resume_version: null,
};

describe('StatusEditor', () => {
  it('shows contract-specific conflict message on 409', async () => {
    vi.spyOn(api, 'patchApplicationStatus').mockRejectedValueOnce(new api.ApiError(409, 'invalid transition', null));

    render(<StatusEditor application={baseApplication} onStatusUpdated={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Target status'), { target: { value: 'drafting' } });
    fireEvent.click(screen.getByRole('button', { name: 'Apply Transition' }));

    await waitFor(() => {
      expect(screen.getByText(/conflicts with the allowed application lifecycle/i)).toBeInTheDocument();
    });
  });
});
