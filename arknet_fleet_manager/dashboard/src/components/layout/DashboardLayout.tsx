import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';
import { Button } from '../ui';

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  currentPath?: string;
}

export function DashboardLayout({
  children,
  title = 'ArkNet Fleet Manager',
  currentPath = '/'
}: DashboardLayoutProps) {
  const { mode, toggleTheme } = useTheme();
  const t = theme.colors[mode];
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Check if we're on mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768); // md breakpoint
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false); // Close mobile menu on desktop
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const navigationItems = [
    { href: '/', label: 'Dashboard', icon: '🏠' },
    { href: '/services', label: 'Services', icon: '⚙️' },
    { href: '/fleet', label: 'Fleet', icon: '🚗' },
    { href: '/analytics', label: 'Analytics', icon: '📊' },
    { href: '/settings', label: 'Settings', icon: '🔧' },
  ];

  const headerStyles: React.CSSProperties = {
    backgroundColor: t.bg.elevated,
    borderBottom: `1px solid ${t.border.default}`,
    padding: `${theme.spacing.md} ${theme.responsive.spacing.container.sm}`,
    boxShadow: theme.shadows.sm,
    position: 'sticky',
    top: 0,
    zIndex: 50,
  };

  const headerContentStyles: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    maxWidth: '1400px',
    margin: '0 auto',
    position: 'relative',
  };

  const titleStyles: React.CSSProperties = {
    fontSize: isMobile ? '1.25rem' : '1.5rem',
    fontWeight: '700',
    color: t.text.primary,
    margin: 0,
  };

  const navStyles: React.CSSProperties = {
    display: isMobile ? 'none' : 'flex',
    gap: theme.spacing.md,
    alignItems: 'center',
  };

  const mobileNavStyles: React.CSSProperties = {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: t.bg.elevated,
    borderBottom: `1px solid ${t.border.default}`,
    boxShadow: theme.shadows.md,
    display: isMobileMenuOpen ? 'flex' : 'none',
    flexDirection: 'column',
    padding: theme.spacing.md,
    gap: theme.spacing.sm,
  };

  const navLinkStyles = (isActive: boolean): React.CSSProperties => ({
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.sm,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderRadius: theme.borderRadius.md,
    textDecoration: 'none',
    color: isActive ? t.interactive.primary.default : t.text.secondary,
    backgroundColor: isActive ? t.interactive.primary.default + '20' : 'transparent',
    fontWeight: isActive ? '600' : '500',
    fontSize: '0.875rem',
    transition: `all ${theme.transitions.fast}`,
    border: `1px solid ${isActive ? t.interactive.primary.default : 'transparent'}`,
    width: isMobile ? '100%' : 'auto',
    justifyContent: isMobile ? 'center' : 'flex-start',
  });

  const hamburgerButtonStyles: React.CSSProperties = {
    display: isMobile ? 'flex' : 'none',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    width: '40px',
    height: '40px',
    backgroundColor: 'transparent',
    border: `1px solid ${t.border.default}`,
    borderRadius: theme.borderRadius.md,
    cursor: 'pointer',
    padding: theme.spacing.sm,
    gap: '3px',
  };

  const hamburgerLineStyles: React.CSSProperties = {
    width: '20px',
    height: '2px',
    backgroundColor: t.text.primary,
    transition: `all ${theme.transitions.fast}`,
    transformOrigin: 'center',
  };

  const headerRightStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.sm,
  };

  const mainStyles: React.CSSProperties = {
    backgroundColor: t.bg.primary,
    minHeight: 'calc(100vh - 65px)',
    padding: theme.responsive.spacing.container.sm,
    transition: `background-color ${theme.transitions.normal}`,
  };

  const containerStyles: React.CSSProperties = {
    maxWidth: '1400px',
    margin: '0 auto',
  };

  // Close mobile menu when clicking outside or on navigation
  const handleNavClick = () => {
    if (isMobile) {
      setIsMobileMenuOpen(false);
    }
  };

  return (
    <div>
      <header style={headerStyles}>
        <div style={headerContentStyles}>
          <Link href="/" style={{ textDecoration: 'none', color: 'inherit' }} onClick={handleNavClick}>
            <h1 style={titleStyles}>{title}</h1>
          </Link>

          {/* Desktop Navigation */}
          <nav style={navStyles}>
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                style={navLinkStyles(currentPath === item.href)}
                onMouseEnter={(e) => {
                  if (currentPath !== item.href) {
                    e.currentTarget.style.backgroundColor = t.bg.tertiary;
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentPath !== item.href) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Mobile Navigation */}
          <nav style={mobileNavStyles}>
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                style={navLinkStyles(currentPath === item.href)}
                onClick={handleNavClick}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          <div style={headerRightStyles}>
            <Button
              variant="ghost"
              size="md"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {mode === 'dark' ? '☀️ Light' : '🌙 Dark'}
            </Button>

            {/* Hamburger Menu Button */}
            <button
              style={hamburgerButtonStyles}
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle navigation menu"
            >
              <div
                style={{
                  ...hamburgerLineStyles,
                  transform: isMobileMenuOpen ? 'rotate(45deg) translate(5px, 5px)' : 'none',
                }}
              />
              <div
                style={{
                  ...hamburgerLineStyles,
                  opacity: isMobileMenuOpen ? 0 : 1,
                }}
              />
              <div
                style={{
                  ...hamburgerLineStyles,
                  transform: isMobileMenuOpen ? 'rotate(-45deg) translate(7px, -6px)' : 'none',
                }}
              />
            </button>
          </div>
        </div>
      </header>

      <main style={mainStyles}>
        <div style={containerStyles}>
          {children}
        </div>
      </main>

      {/* Mobile menu overlay */}
      {isMobile && isMobileMenuOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 40,
          }}
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </div>
  );
}
