import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AsyncBlock } from '../components/AsyncBlock';
import { Layout } from '../components/Layout';
import { ResumeTimeline } from '../components/ResumeTimeline';
import { StatusEditor } from '../components/StatusEditor';
import { getApplicationDetail, getResumeTimeline } from '../lib/api';
import { toStatusLabel } from '../lib/status';
import { ApplicationDetail, ResumeTimelineEntry } from '../types';

export function ApplicationDetailPage() {
  const { applicationId } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [application, setApplication] = useState<ApplicationDetail | null>(null);
  const [timeline, setTimeline] = useState<ResumeTimelineEntry[]>([]);

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
  }, [applicationId]);

  return (
    <Layout title="Application Detail" subtitle="Inspect status lifecycle and resume version history for one application.">
      <p>
        <Link className="ghost-link" to="/applications">
          Back to applications
        </Link>
      </p>

      <AsyncBlock loading={loading} error={error} loadingLabel="Loading application detail...">
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
              </div>
            </section>

            <StatusEditor application={application} onStatusUpdated={setApplication} />
            <ResumeTimeline entries={timeline} />
          </>
        ) : null}
      </AsyncBlock>
    </Layout>
  );
}
