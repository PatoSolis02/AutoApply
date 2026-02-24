import { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';

interface LayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export function Layout({ title, subtitle, children }: LayoutProps) {
  const navItems = [
    { to: '/capture', label: 'Capture' },
    { to: '/applications', label: 'Applications' },
    { to: '/profile', label: 'Profile' },
  ];

  const workflowSteps = ['Capture posting', 'Generate + review', 'Approve + advance status'];

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">AutoApply Workflow</p>
          <h1>{title}</h1>
          <p>{subtitle}</p>
          <p className="tiny muted hero-hint">Workflow: capture the posting, approve a resume version, then move status forward.</p>
        </div>
        <nav className="hero-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink key={item.to} className={({ isActive }) => `ghost-link${isActive ? ' ghost-link-active' : ''}`} to={item.to}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <section className="flow-strip" aria-label="Workflow guide">
        {workflowSteps.map((step, index) => (
          <p key={step} className="flow-step">
            <span className="flow-index">{index + 1}</span>
            {step}
          </p>
        ))}
      </section>
      <main>{children}</main>
    </div>
  );
}
