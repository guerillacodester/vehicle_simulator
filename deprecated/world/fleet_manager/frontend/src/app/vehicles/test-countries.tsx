'use client'

import { useState, useEffect } from 'react'

interface Country {
  id: string
  name: string
}

export default function TestCountries() {
  const [countries, setCountries] = useState<Country[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadCountries = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/countries/')
        const data = await response.json()
        
        const countryOptions = data.map((c: any) => ({
          id: c.country_id,
          name: c.name
        }))
        
        setCountries(countryOptions)
        setLoading(false)
      } catch (err) {
        setError('Failed to load countries')
        setLoading(false)
      }
    }

    loadCountries()
  }, [])

  if (loading) return <div>Loading countries...</div>
  if (error) return <div>Error: {error}</div>

  return (
    <div>
      <h1>Countries Test</h1>
      <p>Found {countries.length} countries:</p>
      <ul>
        {countries.map(country => (
          <li key={country.id}>{country.name}</li>
        ))}
      </ul>
    </div>
  )
}
