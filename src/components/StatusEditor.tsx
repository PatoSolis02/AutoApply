import { FormEvent, useEffect, useMemo, useState } from 'react';
import { ApiError, errorMessageForStatus, patchApplicationStatus } from '../lib/api';
import { getAllowedTargets, toStatusLabel } from '../lib/status';
import { ApplicationDetail, ApplicationStatus } from '../types';

interface StatusEditorProps {
  application: ApplicationDetail;
  onStatusUpdated: (next: ApplicationDetail) => void;
}

export function StatusEditor({ application, onStatusUpdated }: StatusEditorProps) {
  const allowedTargets = useMemo(() => getAllowedTargets(application.status), [application.status]);
  const [targetStatus, setTargetStatus] = useState<ApplicationStatus | ''>('');
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    setTargetStatus('');
    setFeedback(null);
  }, [application.status]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!targetStatus) {
      setFeedback('Choose the next status before applying a transition.');
      return;
    }

    setSaving(true);
    setFeedback(null);

    try {
      const next = await patchApplicationStatus(application.id, targetStatus);
      onStatusUpdated(next);
      setTargetStatus('');
      setFeedback(`Status updated: ${toStatusLabel(application.status)} -> ${toStatusLabel(next.status)}.`);
    } catch (error) {
      if (error instanceof ApiError) {
        setFeedback(error.status === 409 || error.status === 422 ? errorMessageForStatus(error.status) : error.message);
      } else {
        setFeedback('Unexpected error while updating status.');
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel" aria-label="Status transition">
      <h2>Status Transition</h2>
      <p className="muted">Current status: {toStatusLabel(application.status)}</p>
      <p className="tiny muted">Use this after resume review actions are complete to move the workflow forward safely.</p>
      {allowedTargets.length === 0 ? (
        <p className="muted">This application is in a terminal state and cannot transition further.</p>
      ) : (
        <form className="inline-form" onSubmit={onSubmit}>
          <select
            aria-label="Target status"
            value={targetStatus}
            onChange={(event) => setTargetStatus(event.target.value as ApplicationStatus)}
            disabled={saving}
          >
            <option value="">Select target status</option>
            {allowedTargets.map((status) => (
              <option key={status} value={status}>
                {toStatusLabel(status)}
              </option>
            ))}
          </select>
          <button type="submit" disabled={saving || !targetStatus}>
            {saving ? 'Saving...' : 'Apply Transition'}
          </button>
        </form>
      )}
      {feedback ? <p className={feedback.includes('successfully') ? 'notice' : 'error'}>{feedback}</p> : null}
    </section>
  );
}
