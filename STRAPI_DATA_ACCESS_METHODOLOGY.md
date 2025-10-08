# STRAPI API DATA ACCESS METHODOLOGY
**Critical Knowledge for Poisson Spawner Integration**

## Geographic Data Access Protocol
**Date Discovered:** October 8, 2025  
**Context:** Step 2 Validation - Geographic Data Pagination  
**Total Dataset:** 9,702 geographic features confirmed

---

## CRITICAL PAGINATION DISCOVERY

### Strapi API Pagination Limitations
Strapi API **IGNORES** high pagination parameters and enforces a **maximum of 100 records per page**:

```python
# ❌ THESE DON'T WORK - Strapi ignores them
params={"pagination[pageSize]": 50000}  # Still returns 100 records
params={"pagination[limit]": 1000}      # Still returns 100 records
```

### CORRECT Multi-Page Access Method

```python
async def fetch_all_pages(client, endpoint, expected_total):
    """
    PROVEN METHOD: Fetch complete dataset using multi-page iteration
    Used successfully in Step 2 validation - retrieved all 9,702 features
    """
    all_data = []
    page = 1
    max_pages = 100  # Safety limit
    
    while page <= max_pages:
        response = await client.session.get(
            f"{client.base_url}/api/{endpoint}",
            params={
                "pagination[page]": page,
                "pagination[pageSize]": 100  # Strapi's enforced maximum
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            page_data = data.get("data", [])
            all_data.extend(page_data)
            
            # Check pagination metadata for total pages
            pagination = data.get("meta", {}).get("pagination", {})
            total_pages = pagination.get("pageCount", 1)
            
            if page >= total_pages or len(page_data) == 0:
                break
                
            page += 1
        else:
            break
    
    return all_data
```

---

## CONFIRMED DATASET STRUCTURE

### Available Endpoints
- ✅ `/api/pois` - **1,419 POIs** (15 pages)
- ✅ `/api/places` - **8,283 Places** (83 pages)  
- ❌ `/api/landuses` - **404 Not Found** (endpoint doesn't exist)

### Pagination Metadata Format
```json
{
  "data": [...],
  "meta": {
    "pagination": {
      "page": 1,
      "pageSize": 100,
      "pageCount": 15,
      "total": 1419
    }
  }
}
```

---

## VALIDATED ACCESS PATTERNS

### Step 1: API Client Connection
```python
client = StrapiApiClient("http://localhost:1337")
await client.connect()  # Test connectivity first
```

### Step 2: Complete Dataset Retrieval
```python
# Get all POIs (1,419 records across 15 pages)
pois_data = await fetch_all_pages(client, "pois", 1419)

# Get all Places (8,283 records across 83 pages) 
places_data = await fetch_all_pages(client, "places", 8283)

# Total: 9,702 geographic features
total_features = len(pois_data) + len(places_data)
```

### Step 3: Data Structure Access
```python
# Each record contains geographic information
for poi in pois_data:
    poi_id = poi.get('id')
    poi_name = poi.get('name')
    poi_location = poi.get('location')  # Geographic coordinates
    
for place in places_data:
    place_id = place.get('id')
    place_name = place.get('name') 
    place_location = place.get('location')  # Geographic coordinates
```

---

## POISSON SPAWNER INTEGRATION IMPLICATIONS

### Dataset Availability for Statistical Distribution
- **Confirmed Total:** 9,702 geographic features ready for Poisson distribution
- **Spatial Coverage:** Complete Barbados geographic foundation (ID: 29)
- **Access Method:** Multi-page iteration required (not single large request)

### Performance Considerations
- **Page Fetch Time:** ~100ms per page (observed during validation)
- **Total Load Time:** ~9.8 seconds for complete dataset (98 pages)
- **Memory Footprint:** 9,702 records manageable for in-memory processing

### Integration Strategy
1. **Initialization Phase:** Fetch complete dataset once at startup
2. **Caching Strategy:** Store geographic features in memory for Poisson calculations
3. **Update Strategy:** Re-fetch periodically or on-demand basis
4. **Error Handling:** Retry individual pages if fetch fails

---

## CRITICAL SUCCESS CRITERIA MET

✅ **Step 1:** API Client Foundation - 4/4 tests (100%)  
✅ **Step 2:** Geographic Data Pagination - 3/3 tests (100%)  
⏳ **Step 3:** Poisson Mathematical Foundation - PENDING

### Next Integration Steps
1. Validate Poisson mathematics can handle 9,702 features
2. Test geographic coordinate processing for spatial distribution
3. Integrate multi-page data access into spawner architecture
4. Validate end-to-end spawning with complete dataset

---

**This methodology is PROVEN and REQUIRED for accessing the complete geographic dataset in the Poisson spawner integration.**