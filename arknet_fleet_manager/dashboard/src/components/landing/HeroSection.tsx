import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';

interface HeroSectionProps {
  title: string;
  subtitle: string;
}

export function HeroSection({ title, subtitle }: HeroSectionProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const heroStyles = {
    textAlign: 'center' as const,
    marginBottom: theme.spacing['2xl'],
    padding: `0 ${theme.spacing.md}`,
  };

  const titleStyles = {
    fontSize: 'clamp(2rem, 5vw, 3rem)', // Responsive font size
    fontWeight: '700',
    color: t.text.primary,
    marginBottom: theme.spacing.md,
    lineHeight: '1.2',
  };

  const subtitleStyles = {
    fontSize: 'clamp(1rem, 2.5vw, 1.25rem)', // Responsive font size
    color: t.text.secondary,
    maxWidth: '700px',
    margin: '0 auto',
    lineHeight: '1.6',
  };

  return (
    <div style={heroStyles}>
      <h1 style={titleStyles}>{title}</h1>
      <p style={subtitleStyles}>{subtitle}</p>
    </div>
  );
}
