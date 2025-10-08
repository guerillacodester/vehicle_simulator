# DEPOT CONTENT TYPE SCHEMA FIX & DEFAULT DEPOTS
**Critical Fix Required for Step 4 Spawning Validation**

## 🚨 SCHEMA CHANGES REQUIRED

### Current Depot Content Type Issues:
1. **Missing `latitude` field** (spawning system expects `depot.latitude`)
2. **Missing `longitude` field** (spawning system expects `depot.longitude`)  
3. **Nested `location` object** (not directly accessible for coordinate extraction)

### Required Strapi Schema Changes:

#### Add These Fields to Depot Content Type:
```javascript
// In Strapi Admin → Content Types → Depot → Add Fields:

latitude: {
  type: "decimal",
  required: true,
  min: 13.0,
  max: 13.35,
  description: "Latitude coordinate for depot location (Barbados bounds)"
}

longitude: {
  type: "decimal", 
  required: true,
  min: -59.65,
  max: -59.4,
  description: "Longitude coordinate for depot location (Barbados bounds)"
}
```

#### Modify Existing Fields:
```javascript
location: {
  type: "json",
  required: false,  // Make optional for backward compatibility
  description: "DEPRECATED - Use latitude/longitude fields instead"
}
```

---

## 🏗️ DEFAULT DEPOTS TO CREATE

Based on your confirmation (indices 0, 2, 3, 4, 5), create these depots:

### 1. Fix Existing Depot
**Bridgetown Depot (ID: 2)**
- ✅ Keep existing data
- ➕ Add `latitude: 13.0969` 
- ➕ Add `longitude: -59.6168`
- 🔧 Extract from existing `location: {lat: 13.0969, lon: -59.6168}`

### 2. Create New Depots

**DEPOT 1: Speightstown Bus Terminal**
```json
{
  "name": "Speightstown Bus Terminal",
  "depot_id": "SPT_NORTH_01", 
  "latitude": 13.252068,
  "longitude": -59.642543,
  "address": "Speightstown, St. Peter",
  "capacity": 60,
  "is_active": true,
  "is_regional_hub": true
}
```

**DEPOT 2: Granville Williams Bus Terminal**
```json
{
  "name": "Granville Williams Bus Terminal", 
  "depot_id": "BGI_FAIRCHILD_02",
  "latitude": 13.096108,
  "longitude": -59.612344,
  "address": "Fairchild Street, Bridgetown",
  "capacity": 80,
  "is_active": true, 
  "is_regional_hub": true
}
```

**DEPOT 3: Cheapside ZR and Minibus Terminal**
```json
{
  "name": "Cheapside ZR and Minibus Terminal",
  "depot_id": "BGI_CHEAPSIDE_03", 
  "latitude": 13.098168,
  "longitude": -59.621582,
  "address": "Cheapside, Bridgetown",
  "capacity": 70,
  "is_active": true,
  "is_regional_hub": false
}
```

**DEPOT 4: Constitution River Terminal**  
```json
{
  "name": "Constitution River Terminal",
  "depot_id": "BGI_CONSTITUTION_04",
  "latitude": 13.096538, 
  "longitude": -59.608646,
  "address": "Constitution River, Bridgetown",
  "capacity": 50,
  "is_active": true,
  "is_regional_hub": false
}
```

**DEPOT 5: Princess Alice Bus Terminal**
```json
{
  "name": "Princess Alice Bus Terminal",
  "depot_id": "BGI_PRINCESS_05",
  "latitude": 13.097766,
  "longitude": -59.621822, 
  "address": "Princess Alice Highway, Bridgetown",
  "capacity": 65,
  "is_active": true,
  "is_regional_hub": false  
}
```

---

## 📋 IMPLEMENTATION STEPS

### Step 1: Schema Fix (Strapi Admin)
1. Open Strapi Admin → Content Types → Depot
2. Add `latitude` field (decimal, required, min: 13.0, max: 13.35)
3. Add `longitude` field (decimal, required, min: -59.65, max: -59.4)
4. Make `location` field optional (for backward compatibility)
5. Save schema changes

### Step 2: Update Existing Depot (Manual)
1. Open existing "Bridgetown" depot (ID: 2)
2. Add `latitude: 13.0969`
3. Add `longitude: -59.6168` 
4. Save changes

### Step 3: Create New Depots (Manual)
Create 5 new depot entries using the JSON data above

### Step 4: Validate Fix (Automated)
Run Step 4 validation test to confirm spawning system works

---

## 🎯 EXPECTED RESULTS

After schema fix and depot creation:
- ✅ **6 total depots** with proper coordinates
- ✅ **Geographic coverage** across Barbados
- ✅ **Step 4 spawning validation** will pass 4/4 tests
- ✅ **Depot reservoir spawning** operational for real transit simulation

---

## 🚨 CRITICAL DEPENDENCIES

**Step 4 Spawning Validation CANNOT proceed until:**
1. Depot content type schema is fixed (latitude/longitude fields added)
2. Existing depot coordinates are populated
3. New confirmed depots are created

**This schema fix is blocking the complete spawning system integration.**