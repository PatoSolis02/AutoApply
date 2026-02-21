import { Link, useParams } from 'react-router-dom';
import { toStatusLabel } from '../lib/status';
import { ResumeTimelineEntry } from '../types';

interface ResumeTimelineProps {
  entries: ResumeTimelineEntry[];
}

export function ResumeTimeline({ entries }: ResumeTimelineProps) {
  const { applicationId } = useParams();

  if (entries.length === 0) {
    return (
      <section className="panel" aria-label="Resume versions">
        <h2>Resume Versions</h2>
        <p className="muted">No resume versions exist yet for this application.</p>
      </section>
    );
  }

  return (
    <section className="panel" aria-label="Resume versions">
      <h2>Resume Versions</h2>
      <div className="timeline">
        {entries.map((entry) => (
          <article key={entry.id} className="timeline-item">
            <div>
              <p className="mono">{new Date(entry.created_at).toLocaleString()}</p>
              <p className="muted">Template: {entry.template_id}</p>
            </div>
            <div className="timeline-meta">
              <span className={entry.approval.approved ? 'badge good' : 'badge pending'}>
                {entry.approval.approved ? 'Approved' : 'Pending approval'}
              </span>
              <Link to={`/applications/${applicationId}/resume-versions/${entry.id}`}>View detail</Link>
            </div>
          </article>
        ))}
      </div>
      <p className="tiny muted">Ready-to-apply status requires explicit approval for a resume version.</p>
      <p className="tiny muted">Allowed status labels follow contract lifecycle semantics like {toStatusLabel('ready_to_apply')}.</p>
    </section>
  );
}
