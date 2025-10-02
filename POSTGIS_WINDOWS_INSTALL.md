# PostGIS System Installation Guide for Windows

## 🎯 Current Status
- PostgreSQL 17 is installed at: `D:/Program Files/PostgreSQL/17/`
- PostGIS extension is **NOT** installed on the system
- Database: `arknettransit` is ready

---

## 📥 Installation Options

### Option 1: Stack Builder (Recommended - Easiest)

Stack Builder comes with PostgreSQL and makes PostGIS installation simple:

1. **Find Stack Builder:**
   - Start Menu → PostgreSQL 17 → Application Stack Builder
   - OR navigate to: `D:\Program Files\PostgreSQL\17\bin\StackBuilder.exe`

2. **Run Installation:**
   - Select your PostgreSQL installation (localhost:5432)
   - Click "Next"
   - Expand "Spatial Extensions"
   - Check "PostGIS 3.x Bundle for PostgreSQL 17"
   - Click "Next" and follow prompts
   - Default settings are fine
   - Installation takes ~5-10 minutes

3. **Verify Installation:**
   ```powershell
   # Run this after installation
   python scripts/install_postgis.py
   ```

---

### Option 2: Manual Download (If Stack Builder Unavailable)

1. **Download PostGIS:**
   - Go to: https://postgis.net/windows_downloads/
   - Download: PostGIS 3.4.x for PostgreSQL 17 (Windows x64)
   - File will be something like: `postgis-bundle-pg17-3.4.0x64.zip`

2. **Install:**
   - Extract the ZIP file
   - Run `postgis-bundle-pg17-3.4.0x64.exe`
   - Select installation directory: `D:\Program Files\PostgreSQL\17\`
   - Check all components:
     - ☑ PostGIS core
     - ☑ PostGIS Raster
     - ☑ PostGIS Topology
     - ☑ PostGIS SFCGAL
   - Complete installation

3. **Verify Installation:**
   ```powershell
   python scripts/install_postgis.py
   ```

---

### Option 3: PostgreSQL Installer Re-run

If you have the original PostgreSQL installer:

1. Re-run the PostgreSQL 17 installer
2. Choose "Modify" option
3. Select "PostGIS" component
4. Complete installation

---

## ✅ Post-Installation

After installing PostGIS, run:

```powershell
# This will create the extension in your database
python scripts/install_postgis.py
```

Expected output:
```
✅ PostGIS extension created successfully!
   Version: 3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1
✅ Point creation: Working
✅ Distance calculation: Working
✅ GeoJSON support: Working
```

---

## 🔧 Troubleshooting

### "Stack Builder not found"
- Check: `D:\Program Files\PostgreSQL\17\bin\StackBuilder.exe`
- If missing, use Option 2 (Manual Download)

### "Permission denied during installation"
- Right-click installer → Run as Administrator
- Ensure you have admin rights on Windows

### "Wrong PostgreSQL version"
- Verify PostgreSQL version:
  ```powershell
  cd "D:\Program Files\PostgreSQL\17\bin"
  .\psql --version
  ```
- Download matching PostGIS version (must be for PostgreSQL 17)

### "Extension still not found after installation"
- Restart PostgreSQL service:
  ```powershell
  # In PowerShell (as Administrator)
  Restart-Service postgresql-x64-17
  ```
- Check installation path:
  ```powershell
  dir "D:\Program Files\PostgreSQL\17\share\extension\postgis*"
  ```
  Should see: `postgis.control`, `postgis--3.4.0.sql`, etc.

---

## 🎯 What Happens Next

After PostGIS is installed:

1. ✅ Run `python scripts/install_postgis.py` to enable extension
2. ✅ Continue with Strapi content type creation (next step)
3. ✅ Strapi will auto-generate tables with spatial support
4. ✅ Load Barbados GeoJSON data into database

---

## ⏭️ Continue Without PostGIS?

**Yes, you can continue!** PostGIS is not required for the initial Strapi setup:

- Strapi content types will still work
- Geographic data stored as JSON (lat/lon fields)
- PostGIS adds advanced spatial queries later (optional enhancement)

**Recommendation:** Install PostGIS now (10 minutes) to get full spatial capabilities.

---

## 📞 Need Help?

If installation fails:
1. Check PostgreSQL version matches PostGIS version
2. Verify admin rights during installation
3. Check Windows Event Viewer for error details
4. Try PostgreSQL restart after installation

**Continue to next step:** Creating Strapi content types (works with or without PostGIS)
