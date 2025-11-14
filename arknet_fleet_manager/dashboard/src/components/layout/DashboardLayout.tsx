
import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Bus, Building2, Shield, Smartphone } from 'lucide-react';
import { motion } from 'framer-motion';

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  currentPath?: string;
}

export function DashboardLayout({ children, title = 'ArkNet Fleet Manager', currentPath = '/' }: DashboardLayoutProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const navigationItems = [
    { href: '/customer', label: 'Customer', icon: <Bus size={20} color="#00ff88" /> },
    { href: '/operator', label: 'Operator', icon: <Smartphone size={20} color="#00ff88" /> },
    { href: '/agency', label: 'Agency', icon: <Building2 size={20} color="#00ff88" /> },
    { href: '/admin', label: 'Admin', icon: <Shield size={20} color="#00ff88" /> },
  ];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  const headerStyles: React.CSSProperties = {
    backgroundColor: '#0a0a0a',
    borderBottom: '1px solid rgba(255, 199, 38, 0.2)',
    padding: '16px 32px',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    position: 'sticky',
    top: 0,
    zIndex: 50,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  };
  const titleStyles: React.CSSProperties = {
    fontSize: '2.5rem',
    fontWeight: 900,
    color: '#FFC726',
    margin: 0,
    textShadow: '0 0 10px rgba(255, 199, 38, 0.5), 0 0 20px rgba(255, 199, 38, 0.3)',
    letterSpacing: '0.1em',
    flex: 1,
    textAlign: 'center',
    fontFamily: 'Rajdhani, Arial, sans-serif',
    animation: 'pulse 2.5s infinite',
  };
  const mainStyles: React.CSSProperties = {
    backgroundColor: '#000000',
    minHeight: 'calc(100vh - 65px)',
    padding: '32px',
    transition: 'background-color 0.3s',
  };
  const containerStyles: React.CSSProperties = {
    maxWidth: '1400px',
    margin: '0 auto',
  };

  return (
    <motion.div initial={{ opacity: 0, y: -40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1 }}>
      <header style={headerStyles}>
        {/* Logo left */}
        <Link href="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none', color: 'inherit' }}>
          <Image src="/arknet.png" alt="ArkNet Logo" width={48} height={48} style={{ borderRadius: 8, marginRight: 16 }} />
        </Link>
        {/* Neon-glow title center */}
        <h1 style={titleStyles} className="neon-text">{title}</h1>
        {/* Showcase product dropdown menu right */}
        <div ref={dropdownRef} style={{ position: 'relative', marginLeft: 16 }}>
          <button
            type="button"
            style={{ 
              background: '#FFC726', 
              color: '#000000', 
              fontWeight: 700, 
              boxShadow: '0 0 10px rgba(255, 199, 38, 0.5)', 
              borderRadius: '0.375rem',
              padding: '0.625rem 1.25rem',
              border: 'none',
              cursor: 'pointer',
              fontSize: '1rem',
              transition: 'all 0.2s'
            }}
            onClick={() => setDropdownOpen((open) => !open)}
            aria-haspopup="true"
            aria-controls="dashboard-select-menu"
            aria-expanded={dropdownOpen}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#FFD54F';
              e.currentTarget.style.boxShadow = '0 0 15px rgba(255, 199, 38, 0.7)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#FFC726';
              e.currentTarget.style.boxShadow = '0 0 10px rgba(255, 199, 38, 0.5)';
            }}
          >
            Select Dashboard
          </button>
          {dropdownOpen && (
            <div style={{
              position: 'absolute',
              top: '110%',
              right: 0,
              minWidth: 220,
              background: '#0a0a0a',
              border: '1px solid rgba(255, 199, 38, 0.2)',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
              borderRadius: '0.375rem',
              zIndex: 100,
              padding: '8px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }} id="dashboard-select-menu" role="menu">
              {navigationItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 16px',
                    borderRadius: '0.375rem',
                    textDecoration: 'none',
                    color: currentPath === item.href ? '#FFC726' : '#e5e5e5',
                    background: currentPath === item.href ? 'rgba(255, 199, 38, 0.13)' : 'transparent',
                    fontWeight: currentPath === item.href ? 700 : 500,
                    fontSize: '1rem',
                    transition: 'all 0.2s',
                    border: `1px solid ${currentPath === item.href ? '#FFC726' : 'transparent'}`,
                    boxShadow: currentPath === item.href ? '0 0 8px rgba(255, 199, 38, 0.5)' : 'none',
                    cursor: 'pointer',
                  }}
                  onClick={() => setDropdownOpen(false)}
                  role="menuitem"
                >
                  <span style={{ marginRight: 8 }}>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </header>
      <main style={mainStyles}>
        <div style={containerStyles}>{children}</div>
      </main>
    </motion.div>
  );
}
