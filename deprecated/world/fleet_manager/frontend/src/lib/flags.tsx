/**
 * COUNTRY FLAGS UTILITY
 * Centralized flag handling for all components
 */

'use client'

import React, { useState } from 'react';

// Country data cache to avoid repeated API calls
let countryDataCache: Array<{name: {common: string}, cca2: string}> | null = null;

// Fetch country data from REST Countries API
const fetchCountryData = async (): Promise<Array<{name: {common: string}, cca2: string}>> => {
  if (countryDataCache) {
    return countryDataCache;
  }
  
  try {
    const response = await fetch('https://restcountries.com/v3.1/all?fields=name,cca2');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const countries = await response.json();
    countryDataCache = countries;
    console.log(`✅ Loaded ${countries.length} countries from REST Countries API`);
    return countries;
  } catch (error) {
    console.error('❌ Failed to fetch country data from REST Countries API:', error);
    console.warn('⚠️ Country flags and names will not be available until API is accessible');
    // Return empty array instead of hardcoded fallback
    return [];
  }
};

// Get country code from country name using online data
export const getCountryCodeFromName = async (countryName: string): Promise<string> => {
  try {
    const countries = await fetchCountryData();
    const normalizedName = countryName.toLowerCase().trim();
    
    // Find exact or partial match
    const country = countries.find(c => 
      c.name.common.toLowerCase() === normalizedName ||
      c.name.common.toLowerCase().includes(normalizedName) ||
      normalizedName.includes(c.name.common.toLowerCase())
    );
    
    return country ? country.cca2 : '';
  } catch (error) {
    console.warn('Error getting country code:', error);
    return '';
  }
};

// Synchronous version that uses cache only
export const getCountryCodeSync = (countryName: string): string => {
  if (!countryDataCache) {
    console.warn('Country data not loaded yet. Call preloadCountryData() first.');
    return '';
  }
  
  const normalizedName = countryName.toLowerCase().trim();
  
  // Find exact or partial match in cached data
  const country = countryDataCache.find(c => 
    c.name.common.toLowerCase() === normalizedName ||
    c.name.common.toLowerCase().includes(normalizedName) ||
    normalizedName.includes(c.name.common.toLowerCase())
  );
  
  return country ? country.cca2 : '';
};

// Preload country data (call this when app starts)
export const preloadCountryData = () => {
  fetchCountryData().catch(error => {
    console.warn('Failed to preload country data:', error);
  });
};

// Convert country code to Unicode flag emoji dynamically
export const convertToUnicodeFlag = (countryCode: string): string => {
  if (!countryCode || countryCode.length !== 2) return '🏳️';
  
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  
  return String.fromCodePoint(...codePoints);
};

// Extract country code from Unicode flag emoji
export const extractCountryCodeFromFlag = (flag: string): string => {
  if (!flag || flag.length < 2) return '';
  
  try {
    const codePoints = Array.from(flag).map(char => char.codePointAt(0));
    if (codePoints.length >= 2 && codePoints[0] && codePoints[1]) {
      const char1 = String.fromCharCode(codePoints[0] - 127397);
      const char2 = String.fromCharCode(codePoints[1] - 127397);
      return `${char1}${char2}`;
    }
  } catch (e) {
    console.warn('Could not extract country code from flag:', flag);
  }
  
  return '';
};

// Extract country code from label (handles both emoji flags and text)
export const extractCountryCodeFromLabel = (label: string): string => {
  // Try to extract flag emoji from the beginning of the label
  const chars = Array.from(label);
  if (chars.length >= 2) {
    const firstChar = chars[0];
    const secondChar = chars[1];
    
    // Check if the first two characters are flag emojis
    const firstCode = firstChar.codePointAt(0);
    const secondCode = secondChar.codePointAt(0);
    
    if (firstCode && secondCode && 
        firstCode >= 0x1F1E6 && firstCode <= 0x1F1FF &&
        secondCode >= 0x1F1E6 && secondCode <= 0x1F1FF) {
      const flag = firstChar + secondChar;
      const countryCode = extractCountryCodeFromFlag(flag);
      if (countryCode) return countryCode;
    }
  }
  
  // Remove any flag emojis from the beginning and get country name
  let countryName = label;
  
  // Use the same logic as removeFlagsFromText for consistency
  countryName = removeFlagsFromText(countryName).toLowerCase();
  
  // Use cached country data (synchronous)
  return getCountryCodeSync(countryName);
};

// Remove flag emojis from text
export const removeFlagsFromText = (text: string): string => {
  let cleanText = text;
  
  // Remove any Unicode flag emoji at the beginning
  const chars = Array.from(cleanText);
  if (chars.length >= 2) {
    const firstCode = chars[0].codePointAt(0);
    const secondCode = chars[1].codePointAt(0);
    
    // Check if first two chars are flag emojis
    if (firstCode && secondCode && 
        firstCode >= 0x1F1E6 && firstCode <= 0x1F1FF &&
        secondCode >= 0x1F1E6 && secondCode <= 0x1F1FF) {
      cleanText = cleanText.substring(2);
    }
  }
  
  // Remove other flag-like emojis
  if (cleanText.startsWith('🏴')) {
    cleanText = cleanText.substring(2);
  }
  
  return cleanText.trim();
};

// Dynamic flag component
export interface DynamicFlagProps {
  countryCode: string;
  size?: number;
  className?: string;
}

export const DynamicFlag: React.FC<DynamicFlagProps> = ({ 
  countryCode, 
  size = 16, 
  className = '' 
}) => {
  const [flagError, setFlagError] = useState(false);
  
  const flagUrl = `https://flagcdn.com/w40/${countryCode.toLowerCase()}.png`;
  
  if (!flagUrl || flagError) {
    // Fallback to Unicode emoji
    const unicodeFlag = convertToUnicodeFlag(countryCode);
    const sizeClass = size <= 14 ? 'flag-emoji-sm' : 
                     size <= 16 ? 'flag-emoji-md' : 
                     size <= 18 ? 'flag-emoji-lg' : 'flag-emoji-xl';
    
    return (
      <span 
        className={`inline-block ${sizeClass} ${className}`}
      >
        {unicodeFlag}
      </span>
    );
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
