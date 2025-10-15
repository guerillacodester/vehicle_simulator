# Phase 4 Step 1: Manual Collection Creation

## Status: ⏳ WAITING FOR MANUAL STEP

The `operational-configurations` collection needs to be created manually in Strapi Admin UI.

## Instructions:

### 1. Open Strapi Admin
Navigate to: http://localhost:1337/admin

### 2. Go to Content-Type Builder
- Click "Content-Type Builder" in the left sidebar
- Click "+ Create new collection type"

### 3. Configure Collection
**Display name:** `Operational Configuration`  
**API ID (singular):** `operational-configuration`  
**API ID (plural):** `operational-configurations`

Click "Continue"

### 4. Add Fields

#### Field 1: section
- Type: **Text** (short text)
- Name: `section`
- **Required**: ✅ Yes
- Advanced Settings:
  - Regex pattern: (leave empty)
  - Max length: (leave empty)

#### Field 2: parameter
- Type: **Text** (short text)
- Name: `parameter`
- **Required**: ✅ Yes

#### Field 3: value
- Type: **JSON**
- Name: `value`
- **Required**: ✅ Yes

#### Field 4: value_type
- Type: **Enumeration**
- Name: `value_type`
- **Required**: ✅ Yes
- Values (one per line):
  ```
  number
  string
  boolean
  object
  ```

#### Field 5: default_value
- Type: **JSON**
- Name: `default_value`
- **Required**: ✅ Yes

#### Field 6: constraints
- Type: **JSON**
- Name: `constraints`
- Required: ❌ No

#### Field 7: description
- Type: **Text** (long text)
- Name: `description`
- Required: ❌ No

#### Field 8: display_name
- Type: **Text** (short text)
- Name: `display_name`
- Required: ❌ No

#### Field 9: ui_group
- Type: **Text** (short text)
- Name: `ui_group`
- Required: ❌ No

#### Field 10: requires_restart
- Type: **Boolean**
- Name: `requires_restart`
- Required: ❌ No
- Default value: `false`

### 5. Save and Restart
- Click "Save" button
- Wait for Strapi to restart (this may take 30-60 seconds)
- The server will automatically reload

### 6. Configure API Permissions
After Strapi restarts:
- Go to **Settings** → **Roles** → **Public**
- Scroll to **Operational-configuration**
- Enable these permissions:
  - ✅ `find`
  - ✅ `findOne`
  - ✅ `create`
  - ✅ `update`
- Click "Save"

### 7. Verify Creation
Run the test to confirm:
```bash
python test_step1_config_collection.py
```

You should see:
```
❌ Collection Accessibility: PASS
⚠️  No configurations found - collection is empty
```

### 8. Seed Initial Data
Once collection is created and empty:
```bash
cd arknet_fleet_manager
python seed_operational_config.py
```

### 9. Final Verification
Run test again:
```bash
python test_step1_config_collection.py
```

All tests should now PASS! ✅

---

## After Completion

When all tests pass, you can proceed to:
**Step 2: Create Configuration Service Layer**

---

## Troubleshooting

**404 Error**: Collection doesn't exist yet - complete steps above  
**403 Error**: API permissions not enabled - check step 6  
**Empty collection**: Run seed script - step 8
