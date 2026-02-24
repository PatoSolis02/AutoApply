import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AsyncBlock } from '../components/AsyncBlock';
import { Layout } from '../components/Layout';
import { ResumeTimeline } from '../components/ResumeTimeline';
import { StatusEditor } from '../components/StatusEditor';
import {
  ApiError,
  generateResumeVersion,
  getApplicationAuditExport,
  getApplicationDetail,
  getResumeTimeline,
  patchApplicationStatus,
} from '../lib/api';
import { toStatusLabel } from '../lib/status';
import { ApplicationDetail, AuditExportPayload, ResumeTimelineEntry } from '../types';

function formatGenerateError(error: ApiError): string {
  if (error.status !== 422) {
    return error.message || 'Unable to generate resume version right now.';
  }

  if (typeof error.payload === 'object' && error.payload !== null) {
    const detail = (error.payload as { detail?: unknown }).detail;
    if (detail && typeof detail === 'object') {
      const blocked = (detail as { blocked_reasons?: unknown }).blocked_reasons;
      if (Array.isArray(blocked) && blocked.length > 0) {
        return `Generation blocked by compliance checks: ${blocked.map((item) => String(item)).join(' | ')}`;
      }
    }
  }

  return 'Generation blocked by compliance checks. Review profile data and unsupported claims, then try again.';
}

export function ApplicationDetailPage() {
  const { applicationId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [application, setApplication] = useState<ApplicationDetail | null>(null);
  const [timeline, setTimeline] = useState<ResumeTimelineEntry[]>([]);
  const [templateId, setTemplateId] = useState('modern');
  const [generating, setGenerating] = useState(false);
  const [generationMessage, setGenerationMessage] = useState<string | null>(null);
  const [auditExport, setAuditExport] = useState<AuditExportPayload | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  const auditDownloadHref = useMemo(() => {
    if (!auditExport) return null;
    return `data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(auditExport, null, 2))}`;
  }, [auditExport]);

  useEffect(() => {
    if (!applicationId) {
      setError('Application id is missing from route.');
      setLoading(false);
      return;
    }

    let active = true;

    Promise.all([getApplicationDetail(applicationId), getResumeTimeline(applicationId)])
      .then(([detail, versions]) => {
        if (!active) return;
        setApplication(detail);
        setTimeline(versions);
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unable to load application detail.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [applicationId, refreshTick]);

  async function refreshApplicationState(targetApplicationId: string): Promise<void> {
    const [detail, versions] = await Promise.all([getApplicationDetail(targetApplicationId), getResumeTimeline(targetApplicationId)]);
    setApplication(detail);
    setTimeline(versions);
  }

  async function handleGenerateVersion() {
    if (!applicationId || !application) return;

    setGenerating(true);
    setGenerationMessage(null);
    setAuditError(null);

    try {
      if (application.status === 'captured') {
        const drafted = await patchApplicationStatus(applicationId, 'drafting');
        setApplication(drafted);
      }

      const response = await generateResumeVersion(applicationId, templateId.trim() || 'modern');
      await refreshApplicationState(applicationId);

      const warnings = response.warnings.length > 0 ? ` Warnings: ${response.warnings.join(' | ')}` : '';
      setGenerationMessage(`Resume version ${response.resume_version_id} generated.${warnings}`);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setGenerationMessage(formatGenerateError(err));
      } else {
        setGenerationMessage('Unable to generate resume version right now.');
      }
    } finally {
      setGenerating(false);
    }
  }

  async function handleLoadAuditExport() {
    if (!applicationId) return;
    setAuditLoading(true);
    setAuditError(null);

    try {
      const payload = await getApplicationAuditExport(applicationId);
      setAuditExport(payload);
    } catch (err: unknown) {
      setAuditError(err instanceof Error ? err.message : 'Unable to fetch audit export.');
    } finally {
      setAuditLoading(false);
    }
  }

  return (
    <Layout
      title="Application Workspace"
      subtitle="Generate resume versions, handle compliance feedback, and move application status step by step."
    >
      <p>
        <Link className="ghost-link" to="/applications">
          Back to applications
        </Link>
      </p>

      <AsyncBlock
        loading={loading}
        error={error}
        loadingLabel="Loading application detail..."
        errorTitle="Application detail is currently unavailable."
        recoveryHint="Retry after confirming the backend is reachable. If needed, return to the application list and reopen this record."
        onRetry={() => {
          setError(null);
          setLoading(true);
          setRefreshTick((value) => value + 1);
        }}
      >
        {application ? (
          <>
            <section className="panel">
              <h2>{application.role_title}</h2>
              <p className="muted">{application.company}</p>
              <p>
                <span className="badge">{toStatusLabel(application.status)}</span>
              </p>
              <p>{application.notes || 'No notes yet.'}</p>
              <div className="actions-row">
                <a href={application.job_url} target="_blank" rel="noreferrer">
                  Open original posting
                </a>
                <span className="mono">Application ID: {application.id}</span>
                {application.latest_resume_version ? (
                  <Link to={`/applications/${application.id}/resume-versions/${application.latest_resume_version.id}`}>
                    Open latest review
                  </Link>
                ) : null}
              </div>
              <div className="guidance-list">
                <p className="tiny muted">
                  Next: Generate a version, open it for claim review + approval, then use Status Transition to move to Ready To Apply.
                </p>
              </div>
            </section>

            <section className="panel">
              <h2>Generate Resume Version</h2>
              <p className="muted">
                Generation creates a new immutable version with claims map + change log. Approval is still required before{' '}
                {toStatusLabel('ready_to_apply')}.
              </p>
              <div className="inline-form">
                <label className="compact-label" htmlFor="template_id">
                  Template
                </label>
                <input
                  id="template_id"
                  value={templateId}
                  onChange={(event) => setTemplateId(event.target.value)}
                  placeholder="modern"
                />
                <button type="button" onClick={handleGenerateVersion} disabled={generating}>
                  {generating ? 'Generating...' : 'Generate Resume'}
                </button>
              </div>
              <p className="tiny muted">Use template IDs like `modern`. Unknown IDs may fail depending on backend templates.</p>
              {generationMessage ? (
                <p className={generationMessage.includes('generated') ? 'notice' : 'error'}>{generationMessage}</p>
              ) : null}
            </section>

            <StatusEditor application={application} onStatusUpdated={setApplication} />
            <ResumeTimeline entries={timeline} />

            <section className="panel">
              <h2>Audit Export</h2>
              <p className="muted">
                Export a traceable JSON snapshot for this application including capture payload, versions, and approval state.
              </p>
              <div className="actions-row">
                <button type="button" onClick={handleLoadAuditExport} disabled={auditLoading}>
                  {auditLoading ? 'Loading Export...' : 'View Audit Export'}
                </button>
                {auditDownloadHref ? (
                  <a href={auditDownloadHref} download={`audit-${application.id}.json`}>
                    Download JSON
                  </a>
                ) : null}
              </div>
              {auditError ? <p className="error">{auditError}</p> : null}
              {auditExport ? (
                <>
                  <p className="tiny muted">
                    Generated {new Date(auditExport.generated_at).toLocaleString()} with {auditExport.resume_versions.length}{' '}
                    version(s).
                  </p>
                  <pre className="audit-export">{JSON.stringify(auditExport, null, 2)}</pre>
                </>
              ) : null}
            </section>
          </>
        ) : null}
      </AsyncBlock>
    </Layout>
  );
}
