import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';
import { Button } from './ui';

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export function DashboardLayout({ children, title = 'ArkNet Fleet Manager' }: DashboardLayoutProps) {
  const { mode, toggleTheme } = useTheme();
  const t = theme.colors[mode];

  const headerStyles = {
    backgroundColor: t.bg.elevated,
    borderBottom: `1px solid ${t.border.default}`,
    padding: `${theme.spacing.md} ${theme.spacing.xl}`,
    boxShadow: theme.shadows.sm,
    position: 'sticky' as const,
    top: 0,
    zIndex: 10,
  };

  const headerContentStyles = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    maxWidth: '1400px',
    margin: '0 auto',
  };

  const titleStyles = {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: t.text.primary,
    margin: 0,
  };

  const mainStyles = {
    backgroundColor: t.bg.primary,
    minHeight: 'calc(100vh - 65px)',
    padding: theme.spacing.xl,
    transition: `background-color ${theme.transitions.normal}`,
  };

  const containerStyles = {
    maxWidth: '1400px',
    margin: '0 auto',
  };

  return (
    <div>
      <header style={headerStyles}>
        <div style={headerContentStyles}>
          <h1 style={titleStyles}>{title}</h1>
          <Button
            variant="ghost"
            size="md"
            onClick={toggleTheme}
            aria-label="Toggle theme"
          >
            {mode === 'dark' ? '☀️ Light' : '🌙 Dark'}
          </Button>
        </div>
      </header>
      
      <main style={mainStyles}>
        <div style={containerStyles}>
          {children}
        </div>
      </main>
    </div>
  );
}
