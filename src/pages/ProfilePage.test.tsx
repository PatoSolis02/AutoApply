import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProfilePage } from './ProfilePage';
import type { UserProfile } from '../types';
import * as api from '../lib/api';

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api');
  return {
    ...actual,
    getUserProfile: vi.fn(),
    upsertUserProfile: vi.fn(),
  };
});

const getUserProfileMock = vi.mocked(api.getUserProfile);
const upsertUserProfileMock = vi.mocked(api.upsertUserProfile);

const savedProfile: UserProfile = {
  id: 'primary',
  full_name: 'Taylor Dev',
  headline: 'Platform Engineer',
  summary: 'Builds reliable APIs.',
  skills: ['Python', 'TypeScript'],
  experiences: [{ id: 'exp-1', company: 'DataCo' }],
  projects: [{ id: 'proj-1', name: 'AutoApply' }],
  education: [{ id: 'edu-1', school: 'RIT' }],
  updated_at: '2026-02-23T12:00:00Z',
};

function renderProfilePage() {
  render(
    <MemoryRouter>
      <ProfilePage />
    </MemoryRouter>,
  );
}

describe('ProfilePage', () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    getUserProfileMock.mockResolvedValue(savedProfile);
    upsertUserProfileMock.mockResolvedValue(savedProfile);
  });

  it('loads and renders profile values from /profile', async () => {
    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Taylor Dev')).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue('Platform Engineer')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Builds reliable APIs.')).toBeInTheDocument();
    expect((screen.getByLabelText('Skills (newline or comma separated)') as HTMLTextAreaElement).value).toBe(
      'Python\nTypeScript',
    );
  });

  it('shows empty-state notice when /profile returns 404', async () => {
    getUserProfileMock.mockRejectedValueOnce(new api.ApiError(404, 'profile not found', null));

    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByText(/no profile saved yet/i)).toBeInTheDocument();
    });
  });

  it('renders load error for non-404 profile failures', async () => {
    getUserProfileMock.mockRejectedValueOnce(new Error('backend unavailable'));

    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByText('backend unavailable')).toBeInTheDocument();
    });
  });

  it('parses JSON text fields and saves profile payload', async () => {
    getUserProfileMock.mockRejectedValueOnce(new api.ApiError(404, 'missing', null));

    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByText(/no profile saved yet/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Full Name (required)'), { target: { value: '  Jordan Dev  ' } });
    fireEvent.change(screen.getByLabelText('Headline'), { target: { value: '  Staff Engineer ' } });
    fireEvent.change(screen.getByLabelText('Summary'), { target: { value: '  Builds resilient systems. ' } });
    fireEvent.change(screen.getByLabelText('Skills (newline or comma separated)'), {
      target: { value: 'Python, SQL\nReact' },
    });
    fireEvent.change(screen.getByLabelText('Experiences JSON (array of objects)'), {
      target: { value: '[{"id":"exp-2","company":"NewCo"}]' },
    });
    fireEvent.change(screen.getByLabelText('Projects JSON (array of objects)'), {
      target: { value: '[{"id":"proj-2","name":"Workflow Revamp"}]' },
    });
    fireEvent.change(screen.getByLabelText('Education JSON (array of objects)'), {
      target: { value: '[{"id":"edu-2","school":"RIT"}]' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Save Profile' }));

    await waitFor(() => {
      expect(upsertUserProfileMock).toHaveBeenCalledTimes(1);
    });

    expect(upsertUserProfileMock).toHaveBeenCalledWith({
      id: 'primary',
      full_name: 'Jordan Dev',
      headline: 'Staff Engineer',
      summary: 'Builds resilient systems.',
      skills: ['Python', 'SQL', 'React'],
      experiences: [{ id: 'exp-2', company: 'NewCo' }],
      projects: [{ id: 'proj-2', name: 'Workflow Revamp' }],
      education: [{ id: 'edu-2', school: 'RIT' }],
    });

    await waitFor(() => {
      expect(screen.getByText(/profile saved/i)).toBeInTheDocument();
    });
  });

  it('shows JSON validation errors and blocks save request', async () => {
    getUserProfileMock.mockRejectedValueOnce(new api.ApiError(404, 'missing', null));

    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByText(/no profile saved yet/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Full Name (required)'), { target: { value: 'Casey Dev' } });
    fireEvent.change(screen.getByLabelText('Experiences JSON (array of objects)'), { target: { value: '{' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Profile' }));

    await waitFor(() => {
      expect(screen.getByText('Experiences must be valid JSON array text.')).toBeInTheDocument();
    });

    expect(upsertUserProfileMock).not.toHaveBeenCalled();
  });

  it('shows save error when profile write fails', async () => {
    getUserProfileMock.mockRejectedValueOnce(new api.ApiError(404, 'missing', null));
    upsertUserProfileMock.mockRejectedValueOnce(new Error('write failed'));

    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByText(/no profile saved yet/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Full Name (required)'), { target: { value: 'Casey Dev' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Profile' }));

    await waitFor(() => {
      expect(screen.getByText('write failed')).toBeInTheDocument();
    });
  });
});
