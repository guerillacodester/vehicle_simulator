import React from 'react';
// Using arknet global theme colors directly to avoid ThemeProvider dependency

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export function DashboardLayout({ children, title = 'ArkNet Fleet Manager' }: DashboardLayoutProps) {
  // static arknet-like theme values
  const headerStyles = {
    backgroundColor: '#00133f',
    borderBottom: '1px solid rgba(255,255,255,0.04)',
    padding: '1rem 1.5rem',
    boxShadow: '0 2px 6px rgba(0,0,0,0.25)',
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
    color: '#ffffff',
    margin: 0,
  };

  const mainStyles = {
    backgroundColor: '#000b2a',
    minHeight: 'calc(100vh - 65px)',
    padding: '2rem',
    transition: 'background-color 200ms ease',
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
          <div />
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
