import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { beforeAll, beforeEach, describe, expect, it } from 'vitest';
import activeListCardFixture from './fixtures/linkedin/active-list-card.html?raw';
import jsonLdGraphFixture from './fixtures/linkedin/jsonld-graph.html?raw';
import modernTopCardFixture from './fixtures/linkedin/modern-top-card.html?raw';
import topCardTextCompanyMetaFixture from './fixtures/linkedin/top-card-text-company-meta-description.html?raw';
import twoPanePanelFixture from './fixtures/linkedin/two-pane-panel.html?raw';

interface ExtractResponse {
  ok: boolean;
  error?: string;
  data?: {
    title: string;
    company: string;
    location: string | null;
    job_url: string;
    description_raw: string;
  };
}

type RuntimeListener = (
  message: { type?: string },
  sender: unknown,
  sendResponse: (response: ExtractResponse) => void,
) => boolean | void;

let listener: RuntimeListener | null = null;

function installDom(html: string, title: string, url: string) {
  document.documentElement.innerHTML = html;
  document.title = title;
  window.history.replaceState({}, '', url);
}

function runExtractMessage(): Promise<ExtractResponse> {
  if (!listener) {
    throw new Error('Extractor listener was not initialized.');
  }
  const activeListener = listener;

  return new Promise((resolve) => {
    const handledAsAsync = activeListener({ type: 'EXTRACT_JOB' }, {}, (response) => resolve(response));
    if (handledAsAsync !== true) {
      resolve({ ok: false, error: 'Extractor listener did not return async response handle.' });
    }
  });
}

beforeAll(async () => {
  if (!Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'innerText')) {
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      get() {
        return this.textContent ?? '';
      },
      set(value: string) {
        this.textContent = value;
      },
      configurable: true,
    });
  }

  (globalThis as { chrome?: unknown }).chrome = {
    runtime: {
      onMessage: {
        addListener(callback: RuntimeListener) {
          listener = callback;
        },
      },
    },
  };

  const sourcePath = resolve(process.cwd(), 'extension/content.js');
  const source = await readFile(sourcePath, 'utf8');
  window.eval(source);
});

beforeEach(() => {
  document.documentElement.innerHTML = '<head></head><body></body>';
  document.title = 'LinkedIn';
  window.history.replaceState({}, '', 'https://www.linkedin.com/jobs/search/');
});

describe('LinkedIn extractor fixtures', () => {
  it('extracts title/company/location/description from modern top-card layout', async () => {
    installDom(
      modernTopCardFixture,
      'Staff Frontend Engineer | LinkedIn',
      'https://www.linkedin.com/jobs/search/?currentJobId=991122&f_TPR=r86400',
    );

    const response = await runExtractMessage();
    expect(response.ok).toBe(true);
    expect(response.data).toMatchObject({
      title: 'Staff Frontend Engineer',
      company: 'Skyline Labs',
      location: 'San Francisco, CA',
      job_url: 'https://www.linkedin.com/jobs/view/991122',
    });
    expect(response.data?.description_raw).toContain('release safety');
  });

  it('falls back to JobPosting JSON-LD graph for company and description', async () => {
    installDom(
      jsonLdGraphFixture,
      'Platform Engineer | LinkedIn',
      'https://www.linkedin.com/jobs/view/4132/',
    );

    const response = await runExtractMessage();
    expect(response.ok).toBe(true);
    expect(response.data).toMatchObject({
      title: 'Platform Engineer',
      company: 'Northwind Systems',
      location: 'Remote',
      job_url: 'https://www.linkedin.com/jobs/view/4132/',
    });
    expect(response.data?.description_raw).toContain('distributed systems');
  });

  it('uses document title and two-pane panel when company/details nodes vary', async () => {
    installDom(
      twoPanePanelFixture,
      'Senior Reliability Engineer at Nimbus Labs | LinkedIn',
      'https://www.linkedin.com/jobs/view/60012/?trackingId=abc',
    );

    const response = await runExtractMessage();
    expect(response.ok).toBe(true);
    expect(response.data).toMatchObject({
      title: 'Senior Reliability Engineer',
      company: 'Nimbus Labs',
      location: 'Austin, TX',
      job_url: 'https://www.linkedin.com/jobs/view/60012/?trackingId=abc',
    });
    expect(response.data?.description_raw.toLowerCase()).toContain('about the job');
  });

  it('falls back to active list card details when right panel markup is unavailable', async () => {
    installDom(
      activeListCardFixture,
      'LinkedIn',
      'https://www.linkedin.com/jobs/search/?keywords=reliability',
    );

    const response = await runExtractMessage();
    expect(response.ok).toBe(true);
    expect(response.data).toMatchObject({
      title: 'Lead Site Reliability Engineer',
      company: 'Harbor Tech',
      location: 'Boston, MA',
      job_url: 'https://www.linkedin.com/jobs/view/777888/?refId=feed',
    });
    expect(response.data?.description_raw.toLowerCase()).toContain('incident response');
  });

  it('extracts text-only company/location from top-card primary description and uses meta description fallback', async () => {
    installDom(
      topCardTextCompanyMetaFixture,
      'Principal Data Engineer | LinkedIn',
      'https://www.linkedin.com/jobs/search/?currentJobId=889977',
    );

    const response = await runExtractMessage();
    expect(response.ok).toBe(true);
    expect(response.data).toMatchObject({
      title: 'Principal Data Engineer',
      company: 'Fabrikam Analytics',
      location: 'New York, NY',
      job_url: 'https://www.linkedin.com/jobs/view/889977',
    });
    expect(response.data?.description_raw).toContain('streaming data platform');
  });
});
