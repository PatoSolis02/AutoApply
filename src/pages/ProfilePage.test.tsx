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
    getApplications: vi.fn(),
    getUserProfile: vi.fn(),
    uploadResumeToProfile: vi.fn(),
    upsertUserProfile: vi.fn(),
  };
});

const getApplicationsMock = vi.mocked(api.getApplications);
const getUserProfileMock = vi.mocked(api.getUserProfile);
const uploadResumeToProfileMock = vi.mocked(api.uploadResumeToProfile);
const upsertUserProfileMock = vi.mocked(api.upsertUserProfile);

const savedProfile: UserProfile = {
  id: 'primary',
  full_name: 'Taylor Dev',
  headline: 'Platform Engineer',
  summary: 'Builds reliable APIs.',
  skills: ['Python', 'TypeScript'],
  experiences: [
    {
      id: 'exp-1',
      company: 'DataCo',
      title: 'Senior Engineer',
      start_date: '2022-01-01',
      end_date: null,
      bullets: ['Built APIs'],
      skills: ['Python', 'SQL'],
    },
  ],
  projects: [
    {
      id: 'proj-1',
      name: 'AutoApply',
      description: 'Personal productivity tool',
      bullets: ['Shipped v1'],
      skills: ['React'],
      url: 'https://example.com/autoapply',
    },
  ],
  education: [
    {
      id: 'edu-1',
      school: 'RIT',
      degree: 'BS Computer Science',
      field: 'Computer Science',
      start_date: '2018-09-01',
      end_date: '2022-05-01',
    },
  ],
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
    getApplicationsMock.mockResolvedValue({
      items: [
        {
          id: 'app-1',
          company: 'Acme',
          role_title: 'Engineer',
          job_url: 'https://example.com/jobs/1',
          job_source: 'linkedin',
          location: null,
          status: 'captured',
          notes: '',
          fit_score: null,
          created_at: '2026-02-23T12:00:00Z',
          updated_at: '2026-02-23T12:00:00Z',
        },
      ],
      total: 1,
    });
    getUserProfileMock.mockResolvedValue(savedProfile);
    upsertUserProfileMock.mockResolvedValue(savedProfile);
    uploadResumeToProfileMock.mockResolvedValue({
      profile: {
        id: 'primary',
        full_name: 'Upload Parsed Dev',
        headline: 'Platform Engineer',
        summary: 'Parsed from resume.',
        skills: ['Python'],
        experiences: [{ company: 'ParseCo', title: 'Engineer', start_date: '2021-01-01', end_date: null }],
        projects: [],
        education: [],
      },
      warnings: [],
    });
  });

  it('loads and renders profile values from /profile', async () => {
    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByDisplayValue('Taylor Dev')).toBeInTheDocument();
    });

    expect(screen.getByText('Reachable')).toBeInTheDocument();
    expect(screen.getByText('Ready')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Platform Engineer')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Builds reliable APIs.')).toBeInTheDocument();
    expect((screen.getByLabelText('Company 1') as HTMLInputElement).value).toBe('DataCo');
    expect((screen.getByLabelText('Project Name 1') as HTMLInputElement).value).toBe('AutoApply');
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

  it('shows diagnostics failure state when applications signal cannot be read', async () => {
    getApplicationsMock.mockRejectedValueOnce(new Error('applications unavailable'));

    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByText('Unavailable')).toBeInTheDocument();
    });
    expect(screen.getByText('applications unavailable')).toBeInTheDocument();
  });

  it('saves structured profile payload from form sections', async () => {
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
    fireEvent.change(screen.getByLabelText('Company 1'), { target: { value: 'NewCo' } });
    fireEvent.change(screen.getByLabelText('Title 1'), { target: { value: 'Engineer' } });
    fireEvent.change(screen.getByLabelText('Start Date 1'), { target: { value: '2022-01-01' } });
    fireEvent.change(screen.getByLabelText('Experience Skills 1'), { target: { value: 'Python, SQL' } });
    fireEvent.change(screen.getByLabelText('Experience Bullets 1'), { target: { value: 'Built platform APIs' } });

    fireEvent.change(screen.getByLabelText('Project Name 1'), { target: { value: 'Workflow Revamp' } });
    fireEvent.change(screen.getByLabelText('Project Description 1'), { target: { value: 'Automation project' } });
    fireEvent.change(screen.getByLabelText('Project Skills 1'), { target: { value: 'TypeScript, React' } });
    fireEvent.change(screen.getByLabelText('Project URL 1'), { target: { value: 'https://example.com/project' } });
    fireEvent.change(screen.getByLabelText('Project Bullets 1'), { target: { value: 'Cut manual steps by 60%' } });

    fireEvent.change(screen.getByLabelText('School 1'), { target: { value: 'RIT' } });
    fireEvent.change(screen.getByLabelText('Degree 1'), { target: { value: 'BS Computer Science' } });
    fireEvent.change(screen.getByLabelText('Field 1'), { target: { value: 'Computer Science' } });
    fireEvent.change(screen.getByLabelText('Education Start Date 1'), { target: { value: '2018-09-01' } });
    fireEvent.change(screen.getByLabelText('Education End Date 1'), { target: { value: '2022-05-01' } });

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
      experiences: [
        {
          company: 'NewCo',
          title: 'Engineer',
          start_date: '2022-01-01',
          end_date: null,
          bullets: ['Built platform APIs'],
          skills: ['Python', 'SQL'],
        },
      ],
      projects: [
        {
          name: 'Workflow Revamp',
          description: 'Automation project',
          bullets: ['Cut manual steps by 60%'],
          skills: ['TypeScript', 'React'],
          url: 'https://example.com/project',
        },
      ],
      education: [
        {
          school: 'RIT',
          degree: 'BS Computer Science',
          field: 'Computer Science',
          start_date: '2018-09-01',
          end_date: '2022-05-01',
        },
      ],
    });

    await waitFor(() => {
      expect(screen.getByText(/profile saved/i)).toBeInTheDocument();
    });
  });

  it('applies advanced JSON fallback patch into structured fields', async () => {
    getUserProfileMock.mockRejectedValueOnce(new api.ApiError(404, 'missing', null));

    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByText(/no profile saved yet/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Advanced: Raw JSON Fallback'));
    fireEvent.change(screen.getByLabelText('Profile JSON'), {
      target: {
        value: JSON.stringify({
          full_name: 'Casey Dev',
          experiences: [{ company: 'PatchCo', title: 'Engineer' }],
        }),
      },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Apply JSON to Form' }));

    await waitFor(() => {
      expect((screen.getByDisplayValue('Casey Dev') as HTMLInputElement).value).toBe('Casey Dev');
    });
    expect((screen.getByLabelText('Company 1') as HTMLInputElement).value).toBe('PatchCo');
  });

  it('uploads a resume and maps parsed profile values into the form', async () => {
    getUserProfileMock.mockRejectedValueOnce(new api.ApiError(404, 'missing', null));
    uploadResumeToProfileMock.mockResolvedValueOnce({
      profile: {
        id: 'primary',
        full_name: 'Upload Dev',
        headline: 'Parsed Headline',
        summary: 'Parsed summary.',
        skills: ['Go', 'Kubernetes'],
        experiences: [{ company: 'ParseCo', title: 'Engineer', start_date: '2021-01-01', end_date: null }],
        projects: [],
        education: [],
      },
      warnings: ['date normalization incomplete'],
    });

    renderProfilePage();

    await waitFor(() => {
      expect(screen.getByText(/no profile saved yet/i)).toBeInTheDocument();
    });

    const file = new File(['resume-data'], 'resume.pdf', { type: 'application/pdf' });
    fireEvent.change(screen.getByLabelText('Resume file upload'), { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: 'Parse Resume to Form' }));

    await waitFor(() => {
      expect(uploadResumeToProfileMock).toHaveBeenCalledWith(file);
    });

    expect((screen.getByDisplayValue('Upload Dev') as HTMLInputElement).value).toBe('Upload Dev');
    expect((screen.getByLabelText('Company 1') as HTMLInputElement).value).toBe('ParseCo');
    expect(screen.getByText(/date normalization incomplete/i)).toBeInTheDocument();
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
