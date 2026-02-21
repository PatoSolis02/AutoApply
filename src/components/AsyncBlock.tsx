import { ReactNode } from 'react';

interface AsyncBlockProps {
  loading: boolean;
  error: string | null;
  children: ReactNode;
  loadingLabel?: string;
}

export function AsyncBlock({ loading, error, children, loadingLabel = 'Loading...' }: AsyncBlockProps) {
  if (loading) {
    return <p className="panel muted">{loadingLabel}</p>;
  }

  if (error) {
    return <p className="panel error">{error}</p>;
  }

  return <>{children}</>;
}
