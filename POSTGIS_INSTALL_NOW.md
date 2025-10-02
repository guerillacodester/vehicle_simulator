# PostGIS Installation - Quick Start Guide

## ✅ Status Check: Stack Builder Found

Stack Builder is available at: `D:\Program Files\PostgreSQL\17\bin\StackBuilder.exe`

---

## 🚀 Installation Steps (5 minutes)

### Step 1: Launch Stack Builder

Run this command in PowerShell **as Administrator**:

```powershell
& "D:\Program Files\PostgreSQL\17\bin\StackBuilder.exe"
```

Or manually:

1. Right-click on Start Menu → "Run as Administrator"
2. Right-click on Start Menu → "Run as Administrator"
3. Navigate to: `D:\Program Files\PostgreSQL\17\bin\`
4. Double-click `StackBuilder.exe`

---

### Step 2: Select PostgreSQL Installation

1. **Welcome Screen**: Select your PostgreSQL 17 installation
2. Click **Next**

---

### Step 3: Select PostGIS

1. **Available Applications**: Expand "Spatial Extensions"
2. ✅ Check **PostGIS 3.4.x for PostgreSQL 17 x64**
3. Click **Next**

---

### Step 4: Download & Install

1. **Select Directory**: Keep default download location
2. Click **Next** to download
3. **Installation Wizard**: Follow the prompts
   - Accept license agreement
   - Keep default installation directory: `D:\Program Files\PostgreSQL\17\`
   - Select components:
     - ✅ PostGIS core
     - ✅ PostGIS Raster
     - ✅ PostGIS Topology
     - ✅ PostGIS SFCGAL (optional)
     - ✅ Address Standardizer
4. Click **Install**
5. Wait for installation to complete (~2 minutes)

---

### Step 5: Verify Installation

After installation completes, run:

```powershell
python scripts/install_postgis.py
```

**Expected Output:**

```text
✅ PostGIS extension created successfully!
   Version: 3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1
✅ Point creation: Working
✅ Distance calculation: Working
✅ GeoJSON support: Working
```

---

## ⚠️ Troubleshooting

### If Stack Builder doesn't show PostGIS

1. Check internet connection (Stack Builder downloads package list)
2. Try refreshing the application list
3. Use Manual Download method below

### Manual Download (Alternative)

1. Go to: <https://postgis.net/windows_downloads/>
2. Download: **PostGIS 3.4.x for PostgreSQL 17 (Windows x64)**
3. Run the installer
4. Select installation directory: `D:\Program Files\PostgreSQL\17\`
5. Install all components

---

## 🎯 After Installation

Once PostGIS is installed:

1. ✅ Run `python scripts/install_postgis.py` to enable in database
2. ✅ Continue with permissions configuration
3. ✅ Load Barbados GeoJSON data
4. ✅ Test commuter service with geographic spawning

---

## 📞 Need Help?

If installation fails:

- Check you have admin rights
- Verify PostgreSQL 17 is running
- Check Windows Event Viewer for errors
- Ensure PostgreSQL version matches PostGIS version (both must be 17)

---

**Next Step After Installation**: Run the verification script!
