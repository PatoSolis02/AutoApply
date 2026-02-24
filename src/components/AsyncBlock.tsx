import { ReactNode } from 'react';

interface AsyncBlockProps {
  loading: boolean;
  error: string | null;
  children: ReactNode;
  loadingLabel?: string;
  errorTitle?: string;
  recoveryHint?: string;
  retryLabel?: string;
  onRetry?: () => void;
}

export function AsyncBlock({
  loading,
  error,
  children,
  loadingLabel = 'Loading...',
  errorTitle = 'We could not load this section.',
  recoveryHint,
  retryLabel = 'Try Again',
  onRetry,
}: AsyncBlockProps) {
  if (loading) {
    return <p className="panel muted">{loadingLabel}</p>;
  }

  if (error) {
    return (
      <section className="panel async-error">
        <p className="error">{errorTitle}</p>
        <p className="tiny muted">{error}</p>
        {recoveryHint ? <p className="tiny muted">{recoveryHint}</p> : null}
        {onRetry ? (
          <div className="actions-row">
            <button type="button" onClick={onRetry}>
              {retryLabel}
            </button>
          </div>
        ) : null}
      </section>
    );
  }

  return <>{children}</>;
}
