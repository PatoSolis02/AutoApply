import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CapturePage } from './CapturePage';
import * as api from '../lib/api';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api');
  return {
    ...actual,
    captureJob: vi.fn(),
  };
});

const captureJobMock = vi.mocked(api.captureJob);

function renderCaptureRoute() {
  render(
    <MemoryRouter>
      <CapturePage />
    </MemoryRouter>,
  );
}

describe('CapturePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('captures posting and routes to application detail', async () => {
    captureJobMock.mockResolvedValueOnce({
      application_id: 'app-123',
      job_posting_id: 'job-456',
    });

    renderCaptureRoute();

    fireEvent.change(screen.getByLabelText('Role Title'), { target: { value: 'Backend Engineer' } });
    fireEvent.change(screen.getByLabelText('Company'), { target: { value: 'Acme' } });
    fireEvent.change(screen.getByLabelText('Location'), { target: { value: 'Rochester, NY' } });
    fireEvent.change(screen.getByLabelText('Job URL'), { target: { value: 'https://example.com/jobs/1' } });
    fireEvent.change(screen.getByLabelText('Raw Description'), {
      target: { value: 'Build Python APIs and collaborate with product teams.' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Capture Application' }));

    await waitFor(() => {
      expect(captureJobMock).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/applications/app-123');
    });
  });

  it('shows API error message on capture failure', async () => {
    captureJobMock.mockRejectedValueOnce(new api.ApiError(400, 'invalid request payload', null));
    renderCaptureRoute();

    fireEvent.change(screen.getByLabelText('Role Title'), { target: { value: 'Backend Engineer' } });
    fireEvent.change(screen.getByLabelText('Company'), { target: { value: 'Acme' } });
    fireEvent.change(screen.getByLabelText('Job URL'), { target: { value: 'https://example.com/jobs/1' } });
    fireEvent.change(screen.getByLabelText('Raw Description'), { target: { value: 'Build APIs.' } });
    fireEvent.click(screen.getByRole('button', { name: 'Capture Application' }));

    await waitFor(() => {
      expect(screen.getByText(/missing or invalid/i)).toBeInTheDocument();
    });
  });
});
