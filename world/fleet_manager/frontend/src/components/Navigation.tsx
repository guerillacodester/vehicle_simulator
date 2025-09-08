/**
 * NAVIGATION COMPONENT - App Router Navigation
 * Modern navigation component for the App Router with ArkNet branding
 */

'use client'

import React from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import { 
  Home, 
  Truck, 
  Users, 
  Map, 
  Calendar, 
  Clock, 
  Upload,
  Menu,
  X
} from 'lucide-react'
import { CountrySelector } from './country-selector'
import { ThemeToggle } from './theme-toggle'

interface NavigationItem {
  label: string
  href: string
  icon: React.ComponentType<any>
}

const navigationItems: NavigationItem[] = [
  { label: 'Dashboard', href: '/', icon: Home },
  { label: 'Vehicles', href: '/vehicles', icon: Truck },
  { label: 'Drivers', href: '/drivers', icon: Users },
  { label: 'Routes', href: '/routes', icon: Map },
  { label: 'Timetables', href: '/timetables', icon: Calendar },
  { label: 'Scheduling', href: '/scheduling', icon: Clock },
  { label: 'Import Data', href: '/import', icon: Upload },
]

export default function Navigation() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false)
  const pathname = usePathname()

  return (
    <nav className="bg-white dark:bg-gray-900 shadow-lg border-b border-arknet-yellow-300 dark:border-arknet-yellow-600">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center space-x-3">
              <Image
                src="/arknetlogo.png"
                alt="ArkNet Logo"
                width={40}
                height={40}
                className="h-10 w-10"
              />
              <div className="hidden sm:block">
                <div className="text-lg font-bold text-arknet-yellow-600 dark:text-arknet-yellow-400">
                  ArkNet
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 -mt-1">
                  Fleet Manager
                </div>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex space-x-6">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href
              const IconComponent = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-arknet-yellow-100 dark:bg-arknet-yellow-900/50 text-arknet-yellow-800 dark:text-arknet-yellow-200 shadow-sm'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-arknet-yellow-50 dark:hover:bg-gray-800 hover:text-arknet-yellow-700 dark:hover:text-arknet-yellow-300'
                  }`}
                >
                  <IconComponent size={16} />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>

          {/* Right Side Controls */}
          <div className="flex items-center space-x-3">
            {/* Country Selector */}
            <CountrySelector />
            
            {/* Theme Toggle */}
            <ThemeToggle />

            {/* Mobile menu button */}
            <div className="lg:hidden">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-700 dark:text-gray-300 hover:text-arknet-yellow-700 dark:hover:text-arknet-yellow-300 hover:bg-arknet-yellow-50 dark:hover:bg-gray-800 transition-colors"
                aria-expanded="false"
              >
                <span className="sr-only">Open main menu</span>
                {isMobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMobileMenuOpen && (
          <div className="lg:hidden border-t border-arknet-yellow-200 dark:border-arknet-yellow-700">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navigationItems.map((item) => {
                const isActive = pathname === item.href
                const IconComponent = item.icon
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center space-x-3 px-3 py-3 rounded-lg text-base font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-arknet-yellow-100 dark:bg-arknet-yellow-900/50 text-arknet-yellow-800 dark:text-arknet-yellow-200'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-arknet-yellow-50 dark:hover:bg-gray-800 hover:text-arknet-yellow-700 dark:hover:text-arknet-yellow-300'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <IconComponent size={20} />
                    <span>{item.label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
