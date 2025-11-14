import React from 'react';
// Static arknet-like button to avoid ThemeProvider dependency

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
  const baseStyles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    fontWeight: 500,
    borderRadius: '0.5rem',
    transition: 'all 160ms ease',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    border: 'none',
    outline: 'none',
    width: fullWidth ? '100%' : 'auto',
  };

  const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
    sm: { padding: '0.25rem 0.5rem', fontSize: '0.875rem' },
    md: { padding: '0.5rem 0.75rem', fontSize: '1rem' },
    lg: { padding: '0.75rem 1rem', fontSize: '1.125rem' },
  };

  const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
    primary: { backgroundColor: '#FFC726', color: '#000000' },
    secondary: { backgroundColor: 'rgba(255,255,255,0.04)', color: '#ffffff', border: '1px solid rgba(255,255,255,0.06)' },
    success: { backgroundColor: '#22c55e', color: '#ffffff' },
    danger: { backgroundColor: '#ef4444', color: '#ffffff' },
    ghost: { backgroundColor: 'transparent', color: '#ffffff' },
  };

  const combinedStyles = { ...baseStyles, ...sizeStyles[size], ...variantStyles[variant] };

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
