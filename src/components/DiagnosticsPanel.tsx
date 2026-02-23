import { useEffect, useMemo, useState } from 'react';
import { getApplications } from '../lib/api';
import { ApplicationStatus } from '../types';

type ProfileSignal = 'loading' | 'ready' | 'missing' | 'error';

interface DiagnosticsPanelProps {
  profileSignal: ProfileSignal;
}

const STATUS_ORDER: ApplicationStatus[] = [
  'captured',
  'drafting',
  'ready_to_apply',
  'applied',
  'interview',
  'offer',
  'rejected',
];

function zeroStatusCounts(): Record<ApplicationStatus, number> {
  return {
    captured: 0,
    drafting: 0,
    ready_to_apply: 0,
    applied: 0,
    interview: 0,
    offer: 0,
    rejected: 0,
  };
}

function profileBadge(signal: ProfileSignal): { text: string; className: string } {
  if (signal === 'ready') return { text: 'Ready', className: 'badge good' };
  if (signal === 'missing') return { text: 'Missing', className: 'badge pending' };
  if (signal === 'error') return { text: 'Error', className: 'badge danger' };
  return { text: 'Checking', className: 'badge pending' };
}

export function DiagnosticsPanel({ profileSignal }: DiagnosticsPanelProps) {
  const [loading, setLoading] = useState(true);
  const [apiReachable, setApiReachable] = useState<boolean>(false);
  const [apiMessage, setApiMessage] = useState<string | null>(null);
  const [statusCounts, setStatusCounts] = useState<Record<ApplicationStatus, number>>(zeroStatusCounts);
  const [totalApplications, setTotalApplications] = useState<number>(0);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let active = true;

    setLoading(true);
    getApplications()
      .then((payload) => {
        if (!active) return;

        const nextCounts = zeroStatusCounts();
        for (const application of payload.items) {
          nextCounts[application.status] += 1;
        }

        setStatusCounts(nextCounts);
        setTotalApplications(typeof payload.total === 'number' ? payload.total : payload.items.length);
        setApiReachable(true);
        setApiMessage(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setApiReachable(false);
        setApiMessage(err instanceof Error ? err.message : 'Unable to read /applications.');
        setStatusCounts(zeroStatusCounts());
        setTotalApplications(0);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshTick]);

  const profileStatus = profileBadge(profileSignal);
  const lifecycleSnapshot = useMemo(() => {
    const visible = STATUS_ORDER.filter((status) => statusCounts[status] > 0);
    if (visible.length === 0) return 'No application statuses returned.';
    return visible.map((status) => `${status}: ${statusCounts[status]}`).join(' | ');
  }, [statusCounts]);

  return (
    <section className="panel diagnostics-panel" aria-label="Diagnostics">
      <div className="actions-row">
        <h2>Diagnostics</h2>
        <button type="button" onClick={() => setRefreshTick((value) => value + 1)} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
      <p className="tiny muted">Operational backend signals from profile and application endpoints.</p>

      <div className="diagnostics-list">
        <div>
          <p className="tiny muted">Backend API</p>
          <p>
            <span className={apiReachable ? 'badge good' : 'badge danger'}>
              {apiReachable ? 'Reachable' : 'Unavailable'}
            </span>
          </p>
          {apiMessage ? <p className="tiny error">{apiMessage}</p> : null}
        </div>

        <div>
          <p className="tiny muted">Profile Endpoint</p>
          <p>
            <span className={profileStatus.className}>{profileStatus.text}</span>
          </p>
        </div>

        <div>
          <p className="tiny muted">Application Lifecycle</p>
          <p className="tiny mono">total={totalApplications}</p>
          <p className="tiny mono">{lifecycleSnapshot}</p>
        </div>
      </div>
    </section>
  );
}
