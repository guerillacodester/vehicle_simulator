# 🧪 Geofence API Testing Guide

**Created**: October 10, 2025  
**Purpose**: Step-by-step testing of geofence content type and API  
**Estimated Time**: 30-45 minutes

---

## ✅ Step 1: Restart Strapi Server (5 minutes)

### 1.1 Stop Strapi

If Strapi is running, stop it:
- Press `Ctrl+C` in the terminal running Strapi
- Wait for graceful shutdown

### 1.2 Start Strapi

```powershell
cd e:\projects\github\vehicle_simulator\arknet_fleet_manager\arknet-fleet-api
npm run develop
```

### 1.3 Verify Startup

Watch for these log messages:
```
✔ Building build context (XX ms)
✔ Creating admin (XX ms)
...
[2025-10-10 12:00:00.000] info: Server started on http://localhost:1337
```

### 1.4 Check Content Type Registration

Open browser: `http://localhost:1337/admin`

Navigate to: **Content Manager** (left sidebar)

**Expected**: You should see **Geofence** in the collection types list

✅ **Success Criteria**: Geofence appears in Content Manager

❌ **If not visible**: 
- Check for TypeScript compilation errors in terminal
- Verify all files created correctly
- Restart Strapi again

---

## ✅ Step 2: Configure API Permissions (5 minutes)

### 2.1 Navigate to Permissions

1. Click **Settings** (left sidebar, bottom)
2. Click **Users & Permissions** → **Roles**
3. Click **Public** role

### 2.2 Enable Geofence Permissions

Scroll down to **Geofence** section

Enable these checkboxes:
- ☑ `find` (GET /api/geofences)
- ☑ `findOne` (GET /api/geofences/:id)
- ☑ `create` (POST /api/geofences)
- ☑ `update` (PUT /api/geofences/:id)
- ☑ `delete` (DELETE /api/geofences/:id)

Click **Save** (top right)

✅ **Success Criteria**: All 5 permissions enabled for public access

**Note**: For production, you'd restrict create/update/delete to authenticated users only.

---

## ✅ Step 3: Create Test Geofences via Admin UI (10 minutes)

### 3.1 Navigate to Geofences

Click **Content Manager** → **Geofence**

Click **Create new entry** button (top right)

### 3.2 Create Geofence #1: Depot North

Fill in the form:

| Field | Value |
|-------|-------|
| **Name** | Depot North - Boarding Zone |
| **Type** | boarding_zone |
| **Geometry Type** | circle |
| **Center Lat** | -37.8136 |
| **Center Lon** | 145.0123 |
| **Radius Meters** | 80 |
| **Enabled** | ✓ (checked) |
| **Metadata** | `{"capacity": 5, "priority": 10}` |

**Leave blank**:
- Polygon
- Bbox (will auto-compute)
- Routes
- Depots

Click **Save** (top right)

### 3.3 Verify Bbox Auto-Computation

After saving, click the entry you just created

Scroll down to **Bbox** field

**Expected value** (approximately):
```json
[145.01158, -37.81432, 145.01302, -37.81288]
```

✅ **Success Criteria**: Bbox field is populated with 4 numbers [min_lon, min_lat, max_lon, max_lat]

❌ **If bbox is empty**:
- Check Strapi console for lifecycle hook errors
- Verify `lifecycles.js` file exists
- Check JavaScript syntax in lifecycles.js

### 3.4 Create Geofence #2: Depot South

Repeat process with different values:

| Field | Value |
|-------|-------|
| **Name** | Depot South - Boarding Zone |
| **Type** | boarding_zone |
| **Geometry Type** | circle |
| **Center Lat** | -37.8200 |
| **Center Lon** | 145.0200 |
| **Radius Meters** | 100 |
| **Enabled** | ✓ |

### 3.5 Create Geofence #3: Service Area

| Field | Value |
|-------|-------|
| **Name** | Melbourne CBD Service Area |
| **Type** | service_area |
| **Geometry Type** | circle |
| **Center Lat** | -37.8136 |
| **Center Lon** | 144.9631 |
| **Radius Meters** | 5000 |
| **Enabled** | ✓ |

✅ **Success Criteria**: 3 geofences created, all with auto-computed bboxes

---

## ✅ Step 4: Test Update Operation (5 minutes)

### 4.1 Edit Geofence

1. Click on **Depot North - Boarding Zone**
2. Change **Radius Meters** from `80` to `120`
3. Click **Save**

### 4.2 Verify Bbox Recomputed

**Expected**: Bbox values should change (wider bbox due to larger radius)

**Before** (radius=80):
```json
[145.01158, -37.81432, 145.01302, -37.81288]
```

**After** (radius=120):
```json
[145.01122, -37.81468, 145.01338, -37.81252]
```

✅ **Success Criteria**: Bbox updated automatically when radius changed

---

## ✅ Step 5: Test REST API Endpoints (15 minutes)

### 5.1 Setup: Get API Token (Optional for Public Access)

For public endpoints, no token needed. If you enabled authentication:

1. Settings → API Tokens
2. Create New API Token
3. Copy token for use in curl commands

For now, we'll use **public access** (no token required).

### 5.2 Test: List All Geofences

**Request:**
```powershell
curl http://localhost:1337/api/geofences
```

**Expected Response:**
```json
{
  "data": [
    {
      "id": 1,
      "attributes": {
        "name": "Depot North - Boarding Zone",
        "type": "boarding_zone",
        "geometry_type": "circle",
        "center_lat": -37.8136,
        "center_lon": 145.0123,
        "radius_meters": 120,
        "bbox": [145.01122, -37.81468, 145.01338, -37.81252],
        "enabled": true,
        "metadata": {"capacity": 5, "priority": 10},
        "createdAt": "2025-10-10T...",
        "updatedAt": "2025-10-10T..."
      }
    },
    {
      "id": 2,
      "attributes": {
        "name": "Depot South - Boarding Zone",
        ...
      }
    },
    ...
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "pageCount": 1,
      "total": 3
    }
  }
}
```

✅ **Success Criteria**: Returns array of 3 geofences with all attributes

### 5.3 Test: Get Single Geofence

**Request:**
```powershell
curl http://localhost:1337/api/geofences/1
```

**Expected Response:**
```json
{
  "data": {
    "id": 1,
    "attributes": {
      "name": "Depot North - Boarding Zone",
      "type": "boarding_zone",
      ...
    }
  },
  "meta": {}
}
```

✅ **Success Criteria**: Returns single geofence with ID 1

### 5.4 Test: Create Geofence via API

**Request:**
```powershell
curl -X POST http://localhost:1337/api/geofences `
  -H "Content-Type: application/json" `
  -d '{
    \"data\": {
      \"name\": \"Test API Geofence\",
      \"type\": \"custom\",
      \"geometry_type\": \"circle\",
      \"center_lat\": -37.8150,
      \"center_lon\": 145.0150,
      \"radius_meters\": 50,
      \"enabled\": true
    }
  }'
```

**Expected Response:**
```json
{
  "data": {
    "id": 4,
    "attributes": {
      "name": "Test API Geofence",
      "type": "custom",
      "geometry_type": "circle",
      "center_lat": -37.815,
      "center_lon": 145.015,
      "radius_meters": 50,
      "bbox": [145.01455, -37.81545, 145.01545, -37.81455],
      "enabled": true,
      ...
    }
  },
  "meta": {}
}
```

✅ **Success Criteria**: 
- Geofence created with ID 4
- Bbox auto-computed (verify 4 values present)

### 5.5 Test: Update Geofence via API

**Request:**
```powershell
curl -X PUT http://localhost:1337/api/geofences/4 `
  -H "Content-Type: application/json" `
  -d '{
    \"data\": {
      \"radius_meters\": 75
    }
  }'
```

**Expected Response:**
```json
{
  "data": {
    "id": 4,
    "attributes": {
      "name": "Test API Geofence",
      "radius_meters": 75,
      "bbox": [145.01433, -37.81568, 145.01567, -37.81432],
      ...
    }
  }
}
```

✅ **Success Criteria**: 
- Radius updated to 75
- Bbox recomputed (wider than before)

### 5.6 Test: Delete Geofence via API

**Request:**
```powershell
curl -X DELETE http://localhost:1337/api/geofences/4
```

**Expected Response:**
```json
{
  "data": {
    "id": 4,
    "attributes": {
      "name": "Test API Geofence",
      ...
    }
  },
  "meta": {}
}
```

Verify deletion:
```powershell
curl http://localhost:1337/api/geofences
```

**Expected**: Only 3 geofences remain (IDs 1, 2, 3)

✅ **Success Criteria**: Geofence ID 4 deleted successfully

---

## ✅ Step 6: Test Filter Queries (5 minutes)

### 6.1 Filter by Type

**Request:**
```powershell
curl "http://localhost:1337/api/geofences?filters[type][$eq]=boarding_zone"
```

**Expected**: Returns only geofences with type = "boarding_zone" (should be 2)

### 6.2 Filter by Enabled

**Request:**
```powershell
curl "http://localhost:1337/api/geofences?filters[enabled][$eq]=true"
```

**Expected**: Returns all enabled geofences (should be 3)

### 6.3 Filter by Geometry Type

**Request:**
```powershell
curl "http://localhost:1337/api/geofences?filters[geometry_type][$eq]=circle"
```

**Expected**: Returns all circle geofences (should be 3, all circles for now)

✅ **Success Criteria**: All filter queries return correct results

---

## ✅ Step 7: Test Error Handling (5 minutes)

### 7.1 Test: Missing Required Fields

**Request:**
```powershell
curl -X POST http://localhost:1337/api/geofences `
  -H "Content-Type: application/json" `
  -d '{
    \"data\": {
      \"name\": \"Incomplete Geofence\",
      \"type\": \"custom\",
      \"geometry_type\": \"circle\"
    }
  }'
```

**Expected Response**: Error (400 Bad Request)

**Expected Message**:
```json
{
  "error": {
    "status": 400,
    "name": "ValidationError",
    "message": "Circle geofence requires center_lat, center_lon, and radius_meters"
  }
}
```

✅ **Success Criteria**: Validation error returned, geofence not created

### 7.2 Test: Invalid Coordinates

**Request:**
```powershell
curl -X POST http://localhost:1337/api/geofences `
  -H "Content-Type: application/json" `
  -d '{
    \"data\": {
      \"name\": \"Invalid Coords\",
      \"type\": \"custom\",
      \"geometry_type\": \"circle\",
      \"center_lat\": 95.0,
      \"center_lon\": 145.0,
      \"radius_meters\": 100,
      \"enabled\": true
    }
  }'
```

**Expected Response**: Error (400 Bad Request)

**Expected Message**: "center_lat must be between -90 and 90"

✅ **Success Criteria**: Validation prevents invalid latitude

---

## 📋 Complete Testing Checklist

Use this checklist to track your progress:

- [ ] ✅ Step 1.1-1.4: Strapi restarted, geofence content type visible
- [ ] ✅ Step 2.1-2.2: API permissions configured (5 permissions enabled)
- [ ] ✅ Step 3.1-3.5: 3 test geofences created via UI
- [ ] ✅ Step 3.3: Bbox auto-computation verified
- [ ] ✅ Step 4.1-4.2: Update operation + bbox recomputation tested
- [ ] ✅ Step 5.2: GET /api/geofences (list) works
- [ ] ✅ Step 5.3: GET /api/geofences/:id (findOne) works
- [ ] ✅ Step 5.4: POST /api/geofences (create) works + bbox auto-computed
- [ ] ✅ Step 5.5: PUT /api/geofences/:id (update) works + bbox recomputed
- [ ] ✅ Step 5.6: DELETE /api/geofences/:id (delete) works
- [ ] ✅ Step 6.1-6.3: Filter queries work (type, enabled, geometry_type)
- [ ] ✅ Step 7.1-7.2: Error validation works (missing fields, invalid coords)

---

## 🎯 Success Criteria Summary

**All tests pass if:**

1. ✅ Geofence content type appears in Strapi Content Manager
2. ✅ Bbox auto-computes on create (lifecycle hook works)
3. ✅ Bbox recomputes on update (lifecycle hook works)
4. ✅ All 5 REST API endpoints work (find, findOne, create, update, delete)
5. ✅ Filter queries return correct results
6. ✅ Validation errors prevent invalid data
7. ✅ 3 test geofences exist in database

---

## 🐛 Troubleshooting

### Issue: Geofence not visible in Content Manager

**Solution**:
1. Check Strapi console for compilation errors
2. Verify `schema.json` syntax (valid JSON)
3. Restart Strapi completely (stop + start)
4. Clear browser cache and refresh

### Issue: Bbox field is empty

**Solution**:
1. Check Strapi console for lifecycle hook errors
2. Verify `lifecycles.js` exists in correct location
3. Check JavaScript syntax in lifecycles.js
4. Add `console.log()` to lifecycle hooks to debug

### Issue: API permissions not working

**Solution**:
1. Verify permissions saved (click Save button)
2. Check Settings → Users & Permissions → Public → Geofence
3. Try authenticated request with API token
4. Check Strapi console for permission errors

### Issue: Validation errors not working

**Solution**:
1. Verify lifecycle hooks are running (check logs)
2. Test with curl verbose mode: `curl -v ...`
3. Check response status code (should be 400)

---

## 📊 Next Steps After Testing

Once all tests pass:

1. ✅ Mark todo items complete
2. ✅ Document test results
3. ✅ Create sample geofences for actual depots (use real GPS coords)
4. ✅ Move to next phase: Python Strapi client integration
5. ✅ Begin LocationService implementation

---

## 📝 Test Results Log Template

Use this to document your test results:

```
Date: ____________
Tester: ____________

Step 1: Strapi Restart
- [ ] Pass  [ ] Fail  Notes: ________________

Step 2: API Permissions
- [ ] Pass  [ ] Fail  Notes: ________________

Step 3: Create Geofences (UI)
- [ ] Pass  [ ] Fail  Notes: ________________
- Bbox auto-computed: [ ] Yes  [ ] No

Step 4: Update Geofence
- [ ] Pass  [ ] Fail  Notes: ________________
- Bbox recomputed: [ ] Yes  [ ] No

Step 5: REST API Endpoints
- GET /api/geofences: [ ] Pass  [ ] Fail
- GET /api/geofences/:id: [ ] Pass  [ ] Fail
- POST /api/geofences: [ ] Pass  [ ] Fail
- PUT /api/geofences/:id: [ ] Pass  [ ] Fail
- DELETE /api/geofences/:id: [ ] Pass  [ ] Fail

Step 6: Filter Queries
- Filter by type: [ ] Pass  [ ] Fail
- Filter by enabled: [ ] Pass  [ ] Fail
- Filter by geometry_type: [ ] Pass  [ ] Fail

Step 7: Error Handling
- Missing fields: [ ] Pass  [ ] Fail
- Invalid coords: [ ] Pass  [ ] Fail

Overall Result: [ ] ALL PASS  [ ] SOME FAIL

Issues encountered:
_________________________________
_________________________________
_________________________________
```

---

**Ready to test?** Start with Step 1: Restart Strapi!
