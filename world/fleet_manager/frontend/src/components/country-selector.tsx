'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, Globe } from 'lucide-react';

// Dynamic flag component using flag icons from external service
const DynamicFlag = ({ countryCode, size = 20, className = "" }: { 
  countryCode: string; 
  size?: number; 
  className?: string; 
}) => {
  const [flagError, setFlagError] = useState(false);
  
  // Try multiple approaches for flag display
  const flagUrl = `https://flagcdn.com/w20/${countryCode.toLowerCase()}.png`;
  
  if (flagError) {
    // Fallback to Unicode emoji
    const unicodeFlag = convertToUnicodeFlag(countryCode);
    return <span className={`inline-block text-${size === 20 ? 'base' : size === 16 ? 'sm' : 'xs'} ${className}`}>{unicodeFlag}</span>;
  }
  
  return (
    <img 
      src={flagUrl}
      alt={`${countryCode} flag`}
      width={size}
      height={size * 0.67}
      className={`inline-block object-cover ${className}`}
      onError={() => setFlagError(true)}
    />
  );
};

// Convert country code to Unicode flag emoji
const convertToUnicodeFlag = (countryCode: string): string => {
  if (!countryCode || countryCode.length !== 2) return '�️';
  
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  
  return String.fromCodePoint(...codePoints);
};

interface Country {
  country_id: string;
  name: string;
  iso_code: string;
  created_at?: string;
}

interface CountrySelectorProps {
  value?: string;
  onChange?: (countryId: string, countryName: string) => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showFlag?: boolean;
}

const CountrySelector: React.FC<CountrySelectorProps> = ({
  value,
  onChange,
  className = '',
  size = 'md',
  showFlag = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedCountry = countries.find(c => c.country_id === value);

  const sizeClasses = {
    sm: 'h-8 text-xs px-2',
    md: 'h-10 text-sm px-3',
    lg: 'h-12 text-base px-4'
  };

  const iconSizes = {
    sm: 14,
    md: 16,
    lg: 18
  };

  useEffect(() => {
    const loadCountries = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/v1/countries/');
        if (!response.ok) {
          throw new Error(`Failed to load countries: ${response.status}`);
        }
        const data = await response.json();
        
        const uniqueCountries = data.reduce((acc: Country[], country: Country) => {
          if (!acc.find(c => c.country_id === country.country_id)) {
            acc.push(country);
          }
          return acc;
        }, []);
        
        setCountries(uniqueCountries);
        setError(null);
      } catch (err) {
        console.error('Error loading countries:', err);
        setError(err instanceof Error ? err.message : 'Failed to load countries');
      } finally {
        setLoading(false);
      }
    };

    loadCountries();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleCountrySelect = (country: Country) => {
    onChange?.(country.country_id, country.name);
    setIsOpen(false);
  };

  const getFlag = (countryCode: string, size: number = 16): JSX.Element => {
    return <DynamicFlag countryCode={countryCode} size={size} className="mr-2" />;
  };

  const formatCountryDisplay = (country: Country): JSX.Element => {
    if (!showFlag) {
      return <span>{country.name}</span>;
    }
    
    return (
      <span className="flex items-center">
        {getFlag(country.iso_code || country.country_id, iconSizes[size])}
        <span>{country.name}</span>
      </span>
    );
  };

  if (loading) {
    return (
      <div className={`inline-flex items-center ${sizeClasses[size]} ${className} bg-gray-100 dark:bg-gray-700 rounded-md animate-pulse`}>
        <Globe size={iconSizes[size]} className="text-gray-400" />
        <span className="ml-2 text-gray-400">Loading...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`inline-flex items-center ${sizeClasses[size]} ${className} bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded-md`}>
        <Globe size={iconSizes[size]} />
        <span className="ml-2">Error loading countries</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          ${sizeClasses[size]}
          w-full
          bg-white dark:bg-gray-800
          border border-gray-300 dark:border-gray-600
          rounded-md
          shadow-sm
          flex items-center justify-between
          hover:bg-gray-50 dark:hover:bg-gray-700
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          transition-colors duration-200
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : ''}
        `}
      >
        <span className="flex items-center">
          {selectedCountry ? (
            <span className="text-gray-900 dark:text-gray-100">
              {formatCountryDisplay(selectedCountry)}
            </span>
          ) : (
            <span className="text-gray-500 dark:text-gray-400 flex items-center">
              <Globe size={iconSizes[size]} className="mr-2" />
              Select Country
            </span>
          )}
        </span>
        <ChevronDown 
          size={iconSizes[size]} 
          className={`text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
          {countries.length === 0 ? (
            <div className="px-3 py-2 text-gray-500 dark:text-gray-400 text-sm">
              No countries available
            </div>
          ) : (
            countries.map((country) => (
              <button
                key={country.country_id}
                type="button"
                onClick={() => handleCountrySelect(country)}
                className={`
                  w-full px-3 py-2 text-left
                  hover:bg-gray-100 dark:hover:bg-gray-700
                  focus:bg-gray-100 dark:focus:bg-gray-700
                  focus:outline-none
                  text-gray-900 dark:text-gray-100
                  ${value === country.country_id ? 'bg-blue-50 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300' : ''}
                  transition-colors duration-150
                  ${size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm'}
                `}
              >
                {formatCountryDisplay(country)}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default CountrySelector;
