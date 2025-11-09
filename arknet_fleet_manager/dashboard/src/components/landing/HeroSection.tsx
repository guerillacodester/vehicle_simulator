import React from 'react';
// use the arknet global theme colors directly to avoid ThemeProvider dependency

interface HeroSectionProps {
  title: string;
  subtitle: string;
}

export function HeroSection({ title, subtitle }: HeroSectionProps) {
  // static styles aligned with arknet-transit theme
  const heroStyles = {
    textAlign: 'center' as const,
    marginBottom: '2.5rem',
    padding: '0 1rem',
  };

  const titleStyles = {
    fontSize: 'clamp(2rem, 5vw, 3rem)', // Responsive font size
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: '1rem',
    lineHeight: '1.2',
  };

  const subtitleStyles = {
    fontSize: 'clamp(1rem, 2.5vw, 1.25rem)', // Responsive font size
    color: '#cbd5e1',
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
