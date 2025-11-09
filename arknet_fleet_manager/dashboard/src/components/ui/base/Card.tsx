import React from 'react';
// Static arknet-like base Card to avoid ThemeProvider dependency

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  onClick?: () => void;
}

export function Card({
  children,
  className = '',
  padding = 'md',
  hoverable = false,
  onClick,
}: CardProps) {
  const paddingMap = { sm: '0.75rem', md: '1rem', lg: '1.25rem' };

  const styles: React.CSSProperties = {
    backgroundColor: '#07102a',
    border: '1px solid rgba(255,255,255,0.04)',
    borderRadius: '0.75rem',
    padding: paddingMap[padding],
    boxShadow: '0 4px 8px rgba(0,0,0,0.25)',
    transition: 'all 160ms ease',
    cursor: onClick ? 'pointer' : 'default',
  };

  return (
    <div style={styles} className={className} onClick={onClick}>
      {children}
    </div>
  );
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function CardHeader({ children, className = '' }: CardHeaderProps) {
  const styles = { marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.03)' };

  return (
    <div style={styles} className={className}>
      {children}
    </div>
  );
}

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export function CardTitle({ children, className = '', style }: CardTitleProps) {
  const baseStyles = { fontSize: '1.25rem', fontWeight: 600, color: '#ffffff', margin: 0 };

  const combinedStyles = { ...baseStyles, ...style };

  return (
    <h3 style={combinedStyles} className={className}>
      {children}
    </h3>
  );
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export function CardContent({ children, className = '' }: CardContentProps) {
  const styles = { color: '#cbd5e1' };

  return (
    <div style={styles} className={className}>
      {children}
    </div>
  );
}
