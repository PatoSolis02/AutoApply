import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AsyncBlock } from '../components/AsyncBlock';
import { Layout } from '../components/Layout';
import { ApiError, approveResumeVersion, errorMessageForStatus, getResumeVersion } from '../lib/api';
import { ResumeClaim } from '../types';
import { ResumeVersionDetail } from '../types';

function sortClaimsBySeverity(claims: ResumeClaim[]): ResumeClaim[] {
  return [...claims].sort((left, right) => {
    if (left.verification_status === right.verification_status) return 0;
    return left.verification_status === 'rejected' ? -1 : 1;
  });
}

export function ResumeVersionDetailPage() {
  const { applicationId, resumeVersionId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approvalNotice, setApprovalNotice] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [version, setVersion] = useState<ResumeVersionDetail | null>(null);

  useEffect(() => {
    if (!resumeVersionId) {
      setError('Resume version id is missing from route.');
      setLoading(false);
      return;
    }

    let active = true;

    getResumeVersion(resumeVersionId)
      .then((detail) => {
        if (active) setVersion(detail);
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unable to load resume version.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [resumeVersionId]);

  async function handleApprove() {
    if (!resumeVersionId) return;
    setApproving(true);
    setApprovalNotice(null);

    try {
      const updated = await approveResumeVersion(resumeVersionId);
      setVersion(updated);
      setApprovalNotice('Resume version approved. Application can now be marked ready to apply.');
    } catch (err) {
      if (err instanceof ApiError) {
        setApprovalNotice(err.status === 409 || err.status === 422 ? errorMessageForStatus(err.status) : err.message);
      } else {
        setApprovalNotice('Unexpected error while approving this resume.');
      }
    } finally {
      setApproving(false);
    }
  }

  return (
    <Layout title="Resume Version Detail" subtitle="Review change log, claim mappings, and explicit approval state.">
      <p>
        <Link className="ghost-link" to={`/applications/${applicationId}`}>
          Back to application detail
        </Link>
      </p>

      <AsyncBlock loading={loading} error={error} loadingLabel="Loading resume version detail...">
        {version ? (
          <>
            <section className="panel">
              <h2>Version Metadata</h2>
              <p className="mono">Version ID: {version.id}</p>
              <p className="muted">Created: {new Date(version.created_at).toLocaleString()}</p>
              <p className="muted">HTML: {version.rendered_html_path}</p>
              <p className="muted">PDF: {version.pdf_path}</p>
              <p>
                Approval:{' '}
                <span className={version.approval.approved ? 'badge good' : 'badge pending'}>
                  {version.approval.approved ? 'Approved' : 'Pending'}
                </span>
              </p>
              <button type="button" onClick={handleApprove} disabled={approving || version.approval.approved}>
                {version.approval.approved ? 'Approved' : approving ? 'Approving...' : 'Approve Resume Version'}
              </button>
              {approvalNotice ? <p className={approvalNotice.includes('approved') ? 'notice' : 'error'}>{approvalNotice}</p> : null}
            </section>

            <section className="panel">
              <h2>Change Log</h2>
              <p className="tiny muted">
                Total changes tracked: {version.change_log.added.length + version.change_log.removed.length + version.change_log.reworded.length}
              </p>
              <h3>Added</h3>
              <ul>
                {version.change_log.added.length ? (
                  version.change_log.added.map((item) => <li key={`added-${item}`}>{item}</li>)
                ) : (
                  <li className="muted">None</li>
                )}
              </ul>
              <h3>Removed</h3>
              <ul>
                {version.change_log.removed.length ? (
                  version.change_log.removed.map((item) => <li key={`removed-${item}`}>{item}</li>)
                ) : (
                  <li className="muted">None</li>
                )}
              </ul>
              <h3>Reworded</h3>
              <ul>
                {version.change_log.reworded.length ? (
                  version.change_log.reworded.map((item, index) => (
                    <li key={`${item.reason}-${index}`}>
                      <strong>{item.reason}:</strong> {item.from} → {item.to}
                    </li>
                  ))
                ) : (
                  <li className="muted">None</li>
                )}
              </ul>
            </section>

            <section className="panel">
              <h2>Claims Map</h2>
              <p className="tiny mono">
                supported={version.claims_map.filter((claim) => claim.verification_status === 'supported').length} | rejected=
                {version.claims_map.filter((claim) => claim.verification_status === 'rejected').length}
              </p>
              {version.claims_map.length ? (
                <div className="claims-grid">
                  {sortClaimsBySeverity(version.claims_map).map((claim) => (
                    <article
                      className={claim.verification_status === 'supported' ? 'claim-card' : 'claim-card claim-card-danger'}
                      key={claim.bullet_id}
                    >
                      <p>
                        <strong>{claim.bullet_id}</strong>
                      </p>
                      <p>{claim.bullet_text}</p>
                      <p className="muted">
                        Source: {claim.source_type} / {claim.source_id}
                      </p>
                      <p className="muted">Evidence: {claim.evidence_text}</p>
                      <span className={claim.verification_status === 'supported' ? 'badge good' : 'badge danger'}>
                        {claim.verification_status}
                      </span>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted">No claims map entries were produced for this version.</p>
              )}
            </section>
          </>
        ) : null}
      </AsyncBlock>
    </Layout>
  );
}
