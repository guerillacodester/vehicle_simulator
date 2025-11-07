import React from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';

export interface FeatureCardData {
  icon: string;
  title: string;
  description: string;
  href?: string;
  comingSoon?: boolean;
}

interface FeatureCardProps {
  feature: FeatureCardData;
  compact?: boolean;
}

export function FeatureCard({ feature, compact = true }: FeatureCardProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const cardIconStyles = {
    fontSize: compact ? '2.5rem' : '3rem',
    marginBottom: compact ? theme.spacing.sm : theme.spacing.md,
  };

  const cardDescStyles = {
    color: t.text.secondary,
    lineHeight: '1.5',
    fontSize: compact ? '0.875rem' : '1rem',
  };

  const comingSoonStyles = {
    marginTop: compact ? theme.spacing.sm : theme.spacing.md,
    fontSize: '0.875rem',
    color: t.text.tertiary,
    fontStyle: 'italic' as const,
  };

  const linkStyles = {
    textDecoration: 'none',
    color: 'inherit',
    height: '100%', // Ensure link takes full height
  };

  const cardContent = (
    <Card
      hoverable
      compact={compact}
      fixedHeight={compact ? '240px' : '280px'}
      padding={compact ? 'md' : 'lg'}
    >
      <CardHeader>
        <div style={cardIconStyles}>{feature.icon}</div>
        <CardTitle style={{ fontSize: compact ? '1.125rem' : '1.25rem' }}>
          {feature.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p style={cardDescStyles}>{feature.description}</p>
        {feature.comingSoon && (
          <div style={comingSoonStyles}>Coming soon</div>
        )}
      </CardContent>
    </Card>
  );

  if (feature.href && !feature.comingSoon) {
    return (
      <Link href={feature.href} style={linkStyles}>
        {cardContent}
      </Link>
    );
  }

  return cardContent;
}
