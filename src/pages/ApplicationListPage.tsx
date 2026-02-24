import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AsyncBlock } from '../components/AsyncBlock';
import { Layout } from '../components/Layout';
import { getApplications } from '../lib/api';
import { toStatusLabel } from '../lib/status';
import { ApplicationSummary } from '../types';

export function ApplicationListPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;

    getApplications()
      .then((response) => {
        if (active) setApplications(response.items);
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unable to load applications.');
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshTick]);

  return (
    <Layout
      title="Application Tracker"
      subtitle="Open an application workspace, generate and approve resume versions, then move status with confidence."
    >
      <section className="panel">
        <div className="actions-row">
          <p className="muted">
            Start with capture, then use each application detail page for generation, approval checks, and lifecycle updates.
          </p>
          <Link className="ghost-link" to="/capture">
            Capture New Job
          </Link>
        </div>
      </section>
      <AsyncBlock
        loading={loading}
        error={error}
        loadingLabel="Loading applications..."
        errorTitle="Application list unavailable right now."
        recoveryHint="Confirm the backend API is running, then retry. You can still capture a new job while this reloads."
        onRetry={() => {
          setError(null);
          setLoading(true);
          setRefreshTick((value) => value + 1);
        }}
      >
        {applications.length === 0 ? (
          <p className="panel muted">No captured applications yet. Capture a posting to create your first workflow workspace.</p>
        ) : (
          <section className="grid">
            {applications.map((application) => (
              <article className="panel card" key={application.id}>
                <p className="eyebrow">{application.company}</p>
                <h2>{application.role_title}</h2>
                <p className="muted">{application.location ?? 'Location unavailable'}</p>
                <p>
                  <span className="badge">{toStatusLabel(application.status)}</span>
                </p>
                <div className="actions-row">
                  <a href={application.job_url} target="_blank" rel="noreferrer">
                    Original posting
                  </a>
                  <Link to={`/applications/${application.id}`}>View detail</Link>
                </div>
              </article>
            ))}
          </section>
        )}
      </AsyncBlock>
    </Layout>
  );
}
