/**
 * CSS Variable Utilities
 * Helper functions to use CSS variables in React components
 */

/**
 * Get a CSS variable value with rgb() wrapper
 * Example: cssVar('--color-bg-primary') => 'rgb(var(--color-bg-primary))'
 */
export function cssVar(varName: string): string {
  return `rgb(var(${varName}))`;
}

/**
 * Get a CSS variable value with rgba() wrapper and alpha
 * Example: cssVarAlpha('--color-bg-primary', 0.5) => 'rgb(var(--color-bg-primary) / 0.5)'
 */
export function cssVarAlpha(varName: string, alpha: number): string {
  return `rgb(var(${varName}) / ${alpha})`;
}

/**
 * Get a raw CSS variable value
 * Example: cssVarRaw('--shadow-md') => 'var(--shadow-md)'
 */
export function cssVarRaw(varName: string): string {
  return `var(${varName})`;
}

/**
 * Production-grade color tokens for inline styles
 * Use these instead of hardcoded colors
 */
export const colors = {
  // Backgrounds
  bg: {
    primary: 'rgb(var(--color-bg-primary))',
    secondary: 'rgb(var(--color-bg-secondary))',
    tertiary: 'rgb(var(--color-bg-tertiary))',
    elevated: 'rgb(var(--color-bg-elevated))',
    card: 'rgb(var(--color-bg-card))',
    hover: 'rgb(var(--color-bg-hover))',
    active: 'rgb(var(--color-bg-active))',
  },
  
  // Text
  text: {
    primary: 'rgb(var(--color-text-primary))',
    secondary: 'rgb(var(--color-text-secondary))',
    tertiary: 'rgb(var(--color-text-tertiary))',
    quaternary: 'rgb(var(--color-text-quaternary))',
    inverse: 'rgb(var(--color-text-inverse))',
    link: 'rgb(var(--color-text-link))',
    linkHover: 'rgb(var(--color-text-link-hover))',
  },
  
  // Borders
  border: {
    default: 'rgb(var(--color-border-default))',
    subtle: 'rgb(var(--color-border-subtle))',
    hover: 'rgb(var(--color-border-hover))',
    focus: 'rgb(var(--color-border-focus))',
    accent: 'rgb(var(--color-border-accent))',
    error: 'rgb(var(--color-border-error))',
  },
  
  // Status
  status: {
    success: 'rgb(var(--color-success))',
    successHover: 'rgb(var(--color-success-hover))',
    successText: 'rgb(var(--color-success-text))',
    successBg: 'rgb(var(--color-success-bg))',
    
    error: 'rgb(var(--color-error))',
    errorHover: 'rgb(var(--color-error-hover))',
    errorText: 'rgb(var(--color-error-text))',
    errorBg: 'rgb(var(--color-error-bg))',
    
    warning: 'rgb(var(--color-warning))',
    warningHover: 'rgb(var(--color-warning-hover))',
    warningText: 'rgb(var(--color-warning-text))',
    warningBg: 'rgb(var(--color-warning-bg))',
    
    info: 'rgb(var(--color-info))',
    infoHover: 'rgb(var(--color-info-hover))',
    infoText: 'rgb(var(--color-info-text))',
    infoBg: 'rgb(var(--color-info-bg))',
  },
  
  // Interactive
  primary: {
    default: 'rgb(var(--color-primary))',
    hover: 'rgb(var(--color-primary-hover))',
    active: 'rgb(var(--color-primary-active))',
    text: 'rgb(var(--color-primary-text))',
  },
  
  secondary: {
    default: 'rgb(var(--color-secondary))',
    hover: 'rgb(var(--color-secondary-hover))',
    active: 'rgb(var(--color-secondary-active))',
    text: 'rgb(var(--color-secondary-text))',
  },
  
  accent: {
    default: 'rgb(var(--color-accent))',
    hover: 'rgb(var(--color-accent-hover))',
    active: 'rgb(var(--color-accent-active))',
  },
  
  // Disabled
  disabled: {
    bg: 'rgb(var(--color-disabled-bg))',
    text: 'rgb(var(--color-disabled-text))',
    border: 'rgb(var(--color-disabled-border))',
  },
};

/**
 * Production-grade shadow tokens
 */
export const shadows = {
  xs: 'var(--shadow-xs)',
  sm: 'var(--shadow-sm)',
  md: 'var(--shadow-md)',
  lg: 'var(--shadow-lg)',
  xl: 'var(--shadow-xl)',
  button: 'var(--shadow-button)',
  buttonHover: 'var(--shadow-button-hover)',
  card: 'var(--shadow-card)',
  cardHover: 'var(--shadow-card-hover)',
};

/**
 * Example usage in components:
 * 
 * import { colors, shadows } from '@/lib/cssVars';
 * 
 * <div style={{
 *   backgroundColor: colors.bg.card,
 *   color: colors.text.primary,
 *   border: `1px solid ${colors.border.default}`,
 *   boxShadow: shadows.card,
 * }}>
 *   Content
 * </div>
 */
