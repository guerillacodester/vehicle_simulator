/**
 * Theme Configuration
 * Defines color tokens and design system for light and dark modes
 */

export const theme = {
  colors: {
    light: {
      // Background layers
      bg: {
        primary: '#ffffff',
        secondary: '#f8fafc',
        tertiary: '#f1f5f9',
        elevated: '#ffffff',
        card: '#ffffff',
      },
      // Text colors
      text: {
        primary: '#0f172a',
        secondary: '#475569',
        tertiary: '#64748b',
        inverse: '#ffffff',
        accent: '#1e40af',
      },
      // Border colors
      border: {
        default: '#e2e8f0',
        subtle: '#f1f5f9',
        hover: '#cbd5e1',
        focus: '#3b82f6',
        accent: '#1e40af',
      },
      // Status colors
      status: {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6',
        healthy: '#10b981',
        running: '#3b82f6',
        starting: '#f59e0b',
        stopped: '#94a3b8',
        unhealthy: '#ef4444',
        failed: '#dc2626',
      },
      // Interactive elements
      interactive: {
        primary: {
          default: '#1e40af',
          hover: '#1d4ed8',
          pressed: '#1e3a8a',
        },
        success: {
          default: '#059669',
          hover: '#047857',
        },
        danger: {
          default: '#dc2626',
          hover: '#b91c1c',
        },
        accent: {
          default: '#7c3aed',
          hover: '#6d28d9',
        },
        disabled: '#e2e8f0',
      },
      // Gradients
      gradient: {
        primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        accent: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      },
    },
    dark: {
      // Background layers
      bg: {
        primary: '#0f172a',
        secondary: '#1e293b',
        tertiary: '#334155',
        elevated: '#1e293b',
        card: '#1e293b',
      },
      // Text colors
      text: {
        primary: '#f8fafc',
        secondary: '#cbd5e1',
        tertiary: '#64748b',
        inverse: '#0f172a',
        accent: '#60a5fa',
      },
      // Border colors
      border: {
        default: '#334155',
        subtle: '#1e293b',
        hover: '#475569',
        focus: '#60a5fa',
        accent: '#60a5fa',
      },
      // Status colors
      status: {
        success: '#34d399',
        error: '#f87171',
        warning: '#fbbf24',
        info: '#60a5fa',
        healthy: '#34d399',
        running: '#60a5fa',
        starting: '#fbbf24',
        stopped: '#64748b',
        unhealthy: '#f87171',
        failed: '#ef4444',
      },
      // Interactive elements
      interactive: {
        primary: {
          default: '#3b82f6',
          hover: '#2563eb',
          pressed: '#1d4ed8',
        },
        success: {
          default: '#10b981',
          hover: '#059669',
        },
        danger: {
          default: '#ef4444',
          hover: '#dc2626',
        },
        accent: {
          default: '#8b5cf6',
          hover: '#7c3aed',
        },
        disabled: '#334155',
      },
      // Gradients
      gradient: {
        primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        accent: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      },
    },
  },
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
  },
  borderRadius: {
    sm: '0.375rem',  // 6px
    md: '0.5rem',    // 8px
    lg: '0.75rem',   // 12px
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
  },
  transitions: {
    fast: '150ms ease-in-out',
    normal: '200ms ease-in-out',
    slow: '300ms ease-in-out',
  },
  breakpoints: {
    sm: '640px',   // Small devices (phones)
    md: '768px',   // Medium devices (tablets)
    lg: '1024px',  // Large devices (laptops)
    xl: '1280px',  // Extra large devices (desktops)
    '2xl': '1536px', // 2X large devices (large desktops)
  },
  responsive: {
    container: {
      sm: '100%',
      md: '100%',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
    grid: {
      cols: {
        sm: 1,
        md: 2,
        lg: 3,
        xl: 4,
      },
    },
    spacing: {
      container: {
        sm: '1rem',
        md: '1.5rem',
        lg: '2rem',
        xl: '2.5rem',
      },
    },
  },
} as const;

export type Theme = typeof theme;
export type ThemeMode = 'light' | 'dark';
