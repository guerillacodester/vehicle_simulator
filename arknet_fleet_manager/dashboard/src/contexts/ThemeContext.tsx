'use client';

import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { ThemeMode } from '@/lib/theme';

interface ThemeContextType {
  mode: ThemeMode;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const initializedRef = useRef(false);
  const [mode, setMode] = useState<ThemeMode>(() => {
    // Initialize on first render only
    if (typeof window === 'undefined') return 'dark';
    
    const stored = localStorage.getItem('theme') as ThemeMode;
    if (stored === 'light' || stored === 'dark') {
      return stored;
    }
    
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'dark' : 'light';
  });

  // Apply theme on mount and changes
  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
    }
    document.documentElement.setAttribute('data-theme', mode);
    localStorage.setItem('theme', mode);
  }, [mode]);

  const toggleTheme = () => {
    setMode(prev => prev === 'light' ? 'dark' : 'light');
  };

  const setTheme = (newMode: ThemeMode) => {
    setMode(newMode);
  };

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
