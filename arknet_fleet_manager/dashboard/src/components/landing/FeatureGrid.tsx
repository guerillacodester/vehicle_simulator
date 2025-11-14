import React from 'react';
import { theme } from '@/lib/theme';
import { FeatureCard, FeatureCardData } from './FeatureCard';

interface FeatureGridProps {
  features: FeatureCardData[];
  compact?: boolean;
}

export function FeatureGrid({ features, compact = true }: FeatureGridProps) {
  const gridStyles = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: compact ? theme.spacing.md : theme.spacing.lg,
    marginTop: theme.spacing['2xl'],
    alignItems: 'stretch', // Ensure all cards stretch to same height
  };

  return (
    <div style={gridStyles}>
      {features.map((feature, index) => (
        <FeatureCard key={index} feature={feature} compact={compact} />
      ))}
    </div>
  );
}
