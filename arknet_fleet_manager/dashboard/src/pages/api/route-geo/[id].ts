import fs from 'fs/promises'
import path from 'path'
import type { NextApiRequest, NextApiResponse } from 'next'

type GeoJSON = any

// Try candidate base paths so this works when Next is started from different CWDs
function candidateDataDirs(): string[] {
  const cwd = process.cwd()
  return [
    path.resolve(cwd, 'arknet_transit_simulator', 'data'),
    path.resolve(cwd, '..', 'arknet_transit_simulator', 'data'),
    path.resolve(cwd, '..', '..', 'arknet_transit_simulator', 'data'),
  ]
}

async function findGeoJSONForId(id: string): Promise<{filePath: string; content: GeoJSON} | null> {
  const dirs = candidateDataDirs()
  for (const dir of dirs) {
    try {
      const files = await fs.readdir(dir)
      const geoFiles = files.filter(f => f.toLowerCase().endsWith('.geojson'))

      // First attempt: direct filename patterns: route_{id}.geojson or route_{id}.geojson
      const candidates = [
        `route_${id}.geojson`,
        `${id}.geojson`,
        `route-${id}.geojson`,
      ]
      for (const c of candidates) {
        if (geoFiles.includes(c)) {
          const p = path.join(dir, c)
          const text = await fs.readFile(p, 'utf8')
          return { filePath: p, content: JSON.parse(text) }
        }
      }

      // Otherwise scan files and match FeatureCollection.name or a name inside the file
      for (const f of geoFiles) {
        const p = path.join(dir, f)
        try {
          const text = await fs.readFile(p, 'utf8')
          const json = JSON.parse(text)
          // match by explicit name property (e.g., "route_1") or by features metadata
          const name = (json && json.name) || ''
          if (name === `route_${id}` || name === `route-${id}` || name === id) {
            return { filePath: p, content: json }
          }
          // fallback: check if short_name exists in a top-level property
          if (json?.properties?.short_name === id) return { filePath: p, content: json }
        } catch (err) {
          // ignore parse errors for individual files
          continue
        }
      }
    } catch (err) {
      // directory does not exist or is not readable — try next candidate
      continue
    }
  }
  return null
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const rawId = req.query.id
  const id = Array.isArray(rawId) ? rawId[0] : String(rawId || '')
  if (!id) {
    res.status(400).json({ error: 'Missing route id. Use /api/route-geo/1 or /api/route-geo/route_1' })
    return
  }

  const found = await findGeoJSONForId(id)
  if (!found) {
    res.status(404).json({ error: `Canonical geojson for '${id}' not found in arknet_transit_simulator/data` })
    return
  }

  // Serve the canonical GeoJSON directly
  res.setHeader('Content-Type', 'application/geo+json')
  // Cache aggressively in dev? allow short TTL. Production caching should be configured at CDN level.
  res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=3600')
  res.status(200).json(found.content)
}
