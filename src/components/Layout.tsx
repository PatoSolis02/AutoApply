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
          <p className="eyebrow">AutoApply S4-C Workflow</p>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        <nav className="hero-nav" aria-label="Primary">
          <Link className="ghost-link" to="/capture">
            Capture
          </Link>
          <Link className="ghost-link" to="/applications">
            Applications
          </Link>
          <Link className="ghost-link" to="/profile">
            Profile
          </Link>
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
