import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';

type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  children: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  className = '',
  disabled = false,
  children,
  ...props
}: ButtonProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    fontWeight: '500',
    borderRadius: theme.borderRadius.md,
    transition: `all ${theme.transitions.normal}`,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? '0.5' : '1',
    border: 'none',
    outline: 'none',
    width: fullWidth ? '100%' : 'auto',
  };

  const sizeStyles = {
    sm: {
      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
      fontSize: '0.875rem',
    },
    md: {
      padding: `${theme.spacing.sm} ${theme.spacing.md}`,
      fontSize: '1rem',
    },
    lg: {
      padding: `${theme.spacing.md} ${theme.spacing.lg}`,
      fontSize: '1.125rem',
    },
  };

  const variantStyles = {
    primary: {
      backgroundColor: t.interactive.primary.default,
      color: t.text.primary,
      ':hover': {
        backgroundColor: t.interactive.primary.hover,
      },
      ':active': {
        backgroundColor: t.interactive.primary.pressed,
      },
    },
    secondary: {
      backgroundColor: t.bg.secondary,
      color: t.text.primary,
      border: `1px solid ${t.border.default}`,
      ':hover': {
        backgroundColor: t.bg.tertiary,
      },
    },
    success: {
      backgroundColor: t.status.success,
      color: '#fff',
      ':hover': {
        backgroundColor: t.interactive.success.hover,
      },
    },
    danger: {
      backgroundColor: t.status.error,
      color: '#fff',
      ':hover': {
        backgroundColor: t.interactive.danger.hover,
      },
    },
    ghost: {
      backgroundColor: 'transparent',
      color: t.text.primary,
      ':hover': {
        backgroundColor: t.bg.secondary,
      },
    },
  };

  const combinedStyles = {
    ...baseStyles,
    ...sizeStyles[size],
    ...variantStyles[variant],
  };

  return (
    <button
      style={combinedStyles}
      className={className}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
