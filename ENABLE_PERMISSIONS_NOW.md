# ⚡ QUICK FIX: Enable API Permissions in Strapi

## 🎯 Problem
Content types created ✅ but APIs return **403 Forbidden** ❌

## 🚀 Solution (5 Minutes)

### Step 1: Open Strapi Admin
1. Go to: **http://localhost:1337/admin**
2. Login with your admin account

---

### Step 2: Navigate to Roles
1. Click **"Settings"** (⚙️ gear icon in left sidebar)
2. Under **"USERS & PERMISSIONS PLUGIN"** section
3. Click **"Roles"**

You'll see 3 roles:
- Public (unauthenticated access)
- Authenticated (logged-in users)
- Admin (already has all permissions)

---

### Step 3: Configure Public Role

1. Click on **"Public"** role
2. Scroll down to **"Permissions"** section
3. Find these 4 new content types:

**Enable these checkboxes:**

**POI**
- ☑ find
- ☑ findOne

**LANDUSE-ZONE**
- ☑ find
- ☑ findOne

**REGION**
- ☑ find
- ☑ findOne

**SPAWN-CONFIG**
- ☑ find
- ☑ findOne

4. Click **"Save"** button (top right)

---

### Step 4: Configure Authenticated Role

1. Go back to **Settings → Roles**
2. Click on **"Authenticated"** role
3. Scroll to **"Permissions"** section
4. For each content type, **enable ALL permissions:**

**POI** - Check all boxes:
- ☑ count
- ☑ create
- ☑ delete
- ☑ find
- ☑ findOne
- ☑ update

**LANDUSE-ZONE** - Check all boxes:
- ☑ count
- ☑ create
- ☑ delete
- ☑ find
- ☑ findOne
- ☑ update

**REGION** - Check all boxes:
- ☑ count
- ☑ create
- ☑ delete
- ☑ find
- ☑ findOne
- ☑ update

**SPAWN-CONFIG** - Check all boxes:
- ☑ count
- ☑ create
- ☑ delete
- ☑ find
- ☑ findOne
- ☑ update

5. Click **"Save"** button (top right)

---

## ✅ Verify It Works

Test the API in your browser or PowerShell:

```powershell
# Should return empty array (no data yet)
curl http://localhost:1337/api/pois

# Should return empty array
curl http://localhost:1337/api/landuse-zones

# Should return empty array
curl http://localhost:1337/api/regions

# Should return empty array
curl http://localhost:1337/api/spawn-configs
```

**Success Response:**
```json
{
  "data": [],
  "meta": {
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "pageCount": 0,
      "total": 0
    }
  }
}
```

**If you see this, permissions are configured! ✅**

**If you see 403 Forbidden, double-check:**
- Did you click "Save" after enabling permissions?
- Did you enable permissions for the correct role?
- Try refreshing the Strapi admin page

---

## ⏭️ Next Steps

Once APIs are working:

1. **Verify database tables:**
   ```powershell
   python scripts/verify_strapi_tables.py
   ```

2. **Load Barbados data:**
   ```powershell
   python scripts/load_barbados_data.py
   ```

---

## 📸 Visual Guide

**What you're looking for in Strapi Admin:**

```
Settings
├── USERS & PERMISSIONS PLUGIN
│   └── Roles
│       ├── Public
│       │   └── Permissions
│       │       ├── POI
│       │       │   ├── ☑ find
│       │       │   └── ☑ findOne
│       │       ├── LANDUSE-ZONE
│       │       │   ├── ☑ find
│       │       │   └── ☑ findOne
│       │       ├── REGION
│       │       │   ├── ☑ find
│       │       │   └── ☑ findOne
│       │       └── SPAWN-CONFIG
│       │           ├── ☑ find
│       │           └── ☑ findOne
│       │
│       └── Authenticated
│           └── Permissions
│               ├── POI (☑ ALL)
│               ├── LANDUSE-ZONE (☑ ALL)
│               ├── REGION (☑ ALL)
│               └── SPAWN-CONFIG (☑ ALL)
```

---

**Done! Your geographic APIs are now accessible! 🎉**
