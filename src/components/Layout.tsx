import { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface LayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export function Layout({ title, subtitle, children }: LayoutProps) {
  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">AutoApply WS-B</p>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        <Link className="ghost-link" to="/applications">
          Applications
        </Link>
      </header>
      <main>{children}</main>
    </div>
  );
}
