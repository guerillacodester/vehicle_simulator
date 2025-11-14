"use client";

import React from 'react';
// Static arknet-like card implementation to avoid ThemeProvider dependency

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  onClick?: () => void;
  compact?: boolean;
  fixedHeight?: string;
}

export function Card({
  children,
  className = '',
  padding = 'md',
  hoverable = false,
  onClick,
  compact = false,
  fixedHeight,
}: CardProps) {
  const paddingMap = { sm: compact ? '0.5rem' : '0.75rem', md: compact ? '0.75rem' : '1rem', lg: compact ? '1rem' : '1.25rem' };

  const baseStyles: React.CSSProperties = {
    backgroundColor: '#07102a',
    border: '1px solid rgba(255,255,255,0.04)',
    borderRadius: '0.75rem',
    padding: paddingMap[padding],
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.12)',
    transition: 'all 160ms ease',
    cursor: onClick ? 'pointer' : 'default',
    position: 'relative',
    overflow: 'hidden',
    ...(fixedHeight && { height: fixedHeight, display: 'flex', flexDirection: 'column' }),
  };

  // minimal css variables for hover behavior
  const cssVars = { '--hover-shadow': '0 8px 25px rgba(0,0,0,0.15)', '--hover-border': 'rgba(255,255,255,0.06)', '--hover-bg': '#071020' } as React.CSSProperties;

  const combinedClassName = [className, hoverable ? 'hoverable-card' : '']
    .filter(Boolean)
    .join(' ');

  return (
    <div
      style={{ ...baseStyles, ...cssVars }}
      className={combinedClassName}
      onClick={onClick}
    >
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
