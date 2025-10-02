# Strapi API Permissions Configuration Guide

## ⚠️ Issue: Content Types Created but APIs Not Accessible

When new content types are created in Strapi, they are **not automatically enabled** in the API. You must configure permissions for each role.

---

## 🚀 Quick Fix: Automated Script

Run this script to automatically configure permissions:

```powershell
python scripts/configure_strapi_permissions.py
```

**What it does:**
- Logs in as admin
- Gets all roles (Public, Authenticated)
- Enables API permissions for 4 new content types:
  - POI
  - Landuse-zone
  - Region
  - Spawn-config

**Requirements:**
- Strapi must be running
- Admin credentials in `.env` file:
  ```
  ADMIN_EMAIL=admin@arknettransit.com
  ADMIN_PASSWORD=Admin123!
  ```

---

## 🔧 Manual Configuration (If Script Fails)

### Step 1: Open Strapi Admin

1. Navigate to: http://localhost:1337/admin
2. Login with admin credentials

---

### Step 2: Configure Public Role

This allows **unauthenticated** API access (read-only recommended).

1. Go to: **Settings** → **Users & Permissions plugin** → **Roles**
2. Click on **"Public"** role
3. Scroll to **Permissions** section
4. Find each new content type and enable permissions:

#### POI (Point of Interest)
- ✅ **find** - List all POIs
- ✅ **findOne** - Get single POI by ID
- ⬜ create (leave disabled for security)
- ⬜ update (leave disabled for security)
- ⬜ delete (leave disabled for security)

#### LANDUSE-ZONE (Land Use Zone)
- ✅ **find** - List all zones
- ✅ **findOne** - Get single zone by ID
- ⬜ create, update, delete (disabled)

#### REGION (Region/Parish)
- ✅ **find** - List all regions
- ✅ **findOne** - Get single region by ID
- ⬜ create, update, delete (disabled)

#### SPAWN-CONFIG (Spawn Configuration)
- ✅ **find** - List all configs
- ✅ **findOne** - Get single config by ID
- ⬜ create, update, delete (disabled)

5. Click **"Save"** at the top right

---

### Step 3: Configure Authenticated Role

This allows **authenticated users** full CRUD access.

1. Go to: **Settings** → **Users & Permissions plugin** → **Roles**
2. Click on **"Authenticated"** role
3. Scroll to **Permissions** section
4. For each content type, enable **ALL** permissions:

#### POI, LANDUSE-ZONE, REGION, SPAWN-CONFIG
- ✅ **find** - List all
- ✅ **findOne** - Get by ID
- ✅ **create** - Create new records
- ✅ **update** - Update existing records
- ✅ **delete** - Delete records

5. Click **"Save"**

---

## ✅ Verification

### Test Public API Access (No Auth Required)

```powershell
# List all POIs
curl http://localhost:1337/api/pois

# List all land use zones
curl http://localhost:1337/api/landuse-zones

# List all regions
curl http://localhost:1337/api/regions

# List all spawn configs
curl http://localhost:1337/api/spawn-configs
```

**Expected Response:**
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

**Error Response (if permissions not set):**
```json
{
  "error": {
    "status": 403,
    "name": "ForbiddenError",
    "message": "Forbidden"
  }
}
```

---

### Test Authenticated API Access (With Token)

1. **Get API Token:**
   - Strapi Admin → Settings → API Tokens
   - Click **"Create new API Token"**
   - Name: "Data Import"
   - Token type: **"Full access"**
   - Duration: **"Unlimited"**
   - Click **"Save"**
   - Copy the token (shown only once!)

2. **Test POST Request:**
   ```powershell
   $token = "your_api_token_here"
   
   $headers = @{
       "Authorization" = "Bearer $token"
       "Content-Type" = "application/json"
   }
   
   $body = @{
       data = @{
           poi_type = "bus_station"
           name = "Test Bus Stop"
           latitude = 13.0969
           longitude = -59.6202
           spawn_weight = 1.5
           is_active = $true
       }
   } | ConvertTo-Json
   
   Invoke-RestMethod -Uri "http://localhost:1337/api/pois" -Method POST -Headers $headers -Body $body
   ```

**Expected Response:**
```json
{
  "data": {
    "id": 1,
    "attributes": {
      "poi_type": "bus_station",
      "name": "Test Bus Stop",
      "latitude": "13.0969",
      "longitude": "-59.6202",
      "spawn_weight": "1.5",
      "is_active": true,
      ...
    }
  }
}
```

---

## 📊 Permission Matrix

| Content Type | Public (Unauth) | Authenticated | Admin |
|--------------|-----------------|---------------|-------|
| **POI** | find, findOne | ALL | ALL |
| **Landuse-Zone** | find, findOne | ALL | ALL |
| **Region** | find, findOne | ALL | ALL |
| **Spawn-Config** | find, findOne | ALL | ALL |

---

## 🔐 Security Best Practices

### Public Role (Unauthenticated)
✅ **DO:**
- Enable `find` and `findOne` for read-only access
- Allow simulator to query geographic data

❌ **DON'T:**
- Enable `create`, `update`, or `delete` (security risk)
- Anyone on the internet could modify data

### Authenticated Role
✅ **DO:**
- Enable all permissions for authenticated users
- Use for admin tools and data import scripts

🔑 **IMPORTANT:**
- Protect API tokens (don't commit to Git)
- Use environment variables
- Rotate tokens regularly

---

## 🐛 Troubleshooting

### "Forbidden" Error (403)
**Cause:** Permissions not enabled for role

**Fix:**
1. Check role configuration in Strapi Admin
2. Ensure correct permissions are checked
3. Click "Save" after changes
4. Try API request again (no Strapi restart needed)

### "Not Found" Error (404)
**Cause:** Content type doesn't exist or wrong endpoint

**Fix:**
1. Verify table exists: `python scripts/verify_strapi_tables.py`
2. Check endpoint URL (plural form):
   - `/api/pois` (not /api/poi)
   - `/api/landuse-zones` (not /api/landuse-zone)
   - `/api/regions` (not /api/region)
   - `/api/spawn-configs` (not /api/spawn-config)

### Script Login Fails
**Cause:** Wrong admin credentials

**Fix:**
1. Check `.env` file:
   ```
   ADMIN_EMAIL=your_actual_admin_email
   ADMIN_PASSWORD=your_actual_admin_password
   ```
2. Or update script directly:
   ```python
   STRAPI_ADMIN_EMAIL = "admin@arknettransit.com"
   STRAPI_ADMIN_PASSWORD = "Admin123!"
   ```

### Permissions Reset After Restart
**Cause:** Strapi doesn't persist permission changes in some cases

**Fix:**
1. Use database seed files (advanced)
2. Or re-run configuration script after each Strapi restart
3. Or use Strapi CLI to export/import configuration

---

## ⏭️ Next Steps

After configuring permissions:

1. **Verify Tables Created:**
   ```powershell
   python scripts/verify_strapi_tables.py
   ```

2. **Load Barbados Data:**
   ```powershell
   python scripts/load_barbados_data.py
   ```

3. **Test APIs:**
   ```powershell
   # Get all POIs
   curl http://localhost:1337/api/pois
   
   # Get POIs for Barbados
   curl "http://localhost:1337/api/pois?filters[country][code][$eq]=BRB"
   ```

---

## 📚 Resources

- [Strapi Users & Permissions Documentation](https://docs.strapi.io/user-docs/users-roles-permissions)
- [Strapi REST API Documentation](https://docs.strapi.io/dev-docs/api/rest)
- [Strapi API Token Documentation](https://docs.strapi.io/user-docs/settings/API-tokens)

---

**Last Updated:** October 2, 2025
