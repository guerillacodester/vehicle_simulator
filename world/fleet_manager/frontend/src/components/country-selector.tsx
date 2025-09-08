'use client'

import * as React from 'react'
import { Globe, Check } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

interface Country {
  code: string
  name: string
  flag: string
}

const countries: Country[] = [
  { code: 'BB', name: 'Barbados', flag: '🇧🇧' },
  { code: 'JM', name: 'Jamaica', flag: '🇯🇲' },
  { code: 'TT', name: 'Trinidad and Tobago', flag: '🇹🇹' },
  { code: 'GY', name: 'Guyana', flag: '🇬🇾' },
  { code: 'SR', name: 'Suriname', flag: '🇸🇷' },
  { code: 'BS', name: 'Bahamas', flag: '🇧🇸' },
  { code: 'BZ', name: 'Belize', flag: '🇧🇿' },
  { code: 'LC', name: 'Saint Lucia', flag: '🇱🇨' },
  { code: 'GD', name: 'Grenada', flag: '🇬🇩' },
  { code: 'VC', name: 'Saint Vincent and the Grenadines', flag: '🇻🇨' },
]

interface CountrySelectorProps {
  className?: string
}

export function CountrySelector({ className }: CountrySelectorProps) {
  const [selectedCountry, setSelectedCountry] = React.useState<Country>(
    () => {
      if (typeof window !== 'undefined') {
        const saved = localStorage.getItem('arknet-selected-country')
        if (saved) {
          const savedCountry = JSON.parse(saved)
          return countries.find(c => c.code === savedCountry.code) || countries[0]
        }
      }
      return countries[0] // Default to Barbados
    }
  )

  const handleCountrySelect = (country: Country) => {
    setSelectedCountry(country)
    localStorage.setItem('arknet-selected-country', JSON.stringify(country))
    // You can add additional logic here to update the app's context/state
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={cn(
            'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background',
            'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
            'h-10 px-4 py-2',
            // ArkNet branding colors
            'bg-white dark:bg-gray-800 border-yellow-300 dark:border-yellow-600',
            'hover:bg-yellow-50 dark:hover:bg-gray-700',
            'text-gray-700 dark:text-gray-200',
            className
          )}
        >
          <Globe className="h-4 w-4 mr-2" />
          <span className="mr-1">{selectedCountry.flag}</span>
          <span className="hidden sm:inline-block">{selectedCountry.name}</span>
          <span className="sm:hidden">{selectedCountry.code}</span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Select Country</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {countries.map((country) => (
          <DropdownMenuItem
            key={country.code}
            onClick={() => handleCountrySelect(country)}
            className="flex items-center justify-between cursor-pointer"
          >
            <div className="flex items-center">
              <span className="mr-2">{country.flag}</span>
              <span>{country.name}</span>
            </div>
            {selectedCountry.code === country.code && (
              <Check className="h-4 w-4 text-yellow-600" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
