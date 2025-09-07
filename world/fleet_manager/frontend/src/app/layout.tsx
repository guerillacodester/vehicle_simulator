/**
 * ROOT LAYOUT - App Router Layout Component
 * This is the main layout wrapper for the Next.js App Router
 */

import type { Metadata } from 'next'
import Navigation from '@/components/Navigation'
import ConnectionStatus from '@/components/ConnectionStatus'
// TODO: Import font once Next.js is properly set up
// import { Inter } from 'next/font/google'
import './globals.css'

// TODO: Initialize font once Next.js is set up
// const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    template: '%s | Fleet Management System',
    default: 'Fleet Management System',
  },
  description: 'Production-grade fleet management interface for ARK-Net Transit',
  keywords: ['fleet management', 'transportation', 'vehicles', 'drivers', 'scheduling'],
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  // TODO: Convert to actual JSX once React is properly configured
  return (
    <html lang="en">
      <body className="font-inter bg-gray-50">
        <div id="__next" className="fleet-management-app min-h-screen flex flex-col">
          <Navigation />
          <main className="flex-1">
            {children}
          </main>
          <ConnectionStatus />
        </div>
      </body>
    </html>
  )
}
