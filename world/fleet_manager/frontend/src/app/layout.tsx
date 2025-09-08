/**
 * ROOT LAYOUT - App Router Layout Component
 * This is the main layout wrapper for the Next.js App Router with ArkNet theming
 */

import type { Metadata } from 'next'
import Navigation from '@/components/Navigation'
import ConnectionStatus from '@/components/ConnectionStatus'
import { ThemeProvider } from '@/components/theme-provider'
// TODO: Import font once Next.js is properly set up
// import { Inter } from 'next/font/google'
import './globals.css'

// TODO: Initialize font once Next.js is set up
// const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    template: '%s | ArkNet Fleet Manager',
    default: 'ArkNet Fleet Manager',
  },
  description: 'Production-grade fleet management interface for ArkNet Transit - Caribbean transportation solutions',
  keywords: ['fleet management', 'transportation', 'vehicles', 'drivers', 'scheduling', 'ArkNet', 'Caribbean'],
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-inter bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <ThemeProvider
          defaultTheme="system"
          storageKey="arknet-ui-theme"
        >
          <div id="__next" className="fleet-management-app min-h-screen flex flex-col">
            <Navigation />
            <main className="flex-1 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
              {children}
            </main>
            <ConnectionStatus />
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
