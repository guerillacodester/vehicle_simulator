# Poisson-Based GeoJSON Passenger Spawning System

## 🎲 **Statistical Passenger Spawning with Real Geographic Data**

This system uses **Poisson distribution** for realistic passenger spawning based on actual GeoJSON population and land use data, providing statistically accurate passenger patterns.

---

## 📊 **Poisson Distribution Benefits**

### **Why Poisson?**

- **Realistic Randomness**: Models natural passenger arrival patterns
- **Statistical Accuracy**: Follows real-world transit usage patterns  
- **Time-Based Variation**: Different rates for rush hour vs off-peak
- **Geographic Weighting**: Higher spawns in dense population areas

### **Mathematical Foundation**

```python
# Poisson formula: P(X = k) = (λ^k * e^(-λ)) / k!
# λ (lambda) = mean arrival rate per time period
# k = actual number of passengers spawned

passenger_count = np.random.poisson(spawn_rate)
```

---

## 🗺️ **GeoJSON Data Integration**

### **Simplified File Structure** ✅

```text
passenger_service/
├── geojson_data/
│   ├── barbados_landuse.geojson      # Population zones
│   ├── barbados_amenities.geojson    # Activity centers  
│   ├── barbados_names.geojson        # Place names
│   ├── barbados_busstops.geojson     # Transport hubs
│   └── barbados_highway.geojson      # Transport network
├── poisson_geojson_spawner.py        # Main spawning system
└── strapi_api_client.py              # API integration
```

### **Data Processing Pipeline**

1. **Load GeoJSON Files** → Parse geographic features
2. **Calculate Population Density** → Estimate spawn rates per zone
3. **Apply Time Modifiers** → Rush hour vs off-peak multipliers
4. **Generate Poisson Spawns** → Statistical passenger counts
5. **Match to Routes** → Assign nearest transit routes

---

## 🏙️ **Population Zone Types**

### **Residential Zones**

- **Land Use**: `residential`, `urban`, `suburban`, `village`
- **Population Density**: 800-4000 people/km²
- **Peak Hours**: 7-9 AM (outbound), 5-7 PM (inbound)
- **Trip Purposes**: Work commute, school, shopping

### **Commercial Zones**

- **Land Use**: `commercial`, `retail`, `office`, `mixed`
- **Activity Level**: 500-1200 workers/visitors per km²
- **Peak Hours**: 9 AM - 5 PM (business hours)
- **Trip Purposes**: Work, business meetings, shopping

### **Amenity Zones**

- **Types**: Schools, hospitals, shopping centers, beaches
- **Activity Multipliers**: 0.5x - 6.0x base rate
- **Specific Peak Hours**: School (7-8 AM, 3-4 PM), Shopping (10 AM-2 PM, 5-7 PM)
- **Trip Purposes**: Education, medical, recreation, tourism

---

## ⏰ **Time-Based Spawn Modulation**

### **Rush Hour Patterns**

```python
# Morning Rush (7-9 AM): 2.5x multiplier
# Evening Rush (5-7 PM): 2.5x multiplier  
# Lunch Time (12-2 PM): 1.2x multiplier
# Night Time (10 PM-6 AM): 0.2x multiplier
# Regular Hours: 1.0x base rate
```

### **Zone-Specific Time Patterns**

- **Residential**: High morning outbound, high evening inbound
- **Commercial**: Steady during business hours, low at night
- **Schools**: Sharp peaks at start/end of school day
- **Shopping**: Higher on weekends and evenings
- **Tourism**: Daytime peaks, seasonal variation

---

## 🎯 **Spawn Rate Calculations**

### **Poisson Lambda (λ) Calculation**

```python
base_rate = population_density * 0.1          # Base passengers/hour
peak_multiplier = 2.5 if rush_hour else 1.0   # Time modifier
zone_modifier = get_zone_modifier(zone_type)   # Zone-specific modifier

hourly_rate = base_rate * peak_multiplier * zone_modifier
lambda_rate = hourly_rate * (time_window_minutes / 60.0)

passenger_count = np.random.poisson(lambda_rate)
```

### **Example Spawn Rates**

- **Dense Residential (Rush Hour)**: λ = 8.0 → 6-12 passengers/5min
- **Commercial District (Business Hours)**: λ = 5.0 → 3-8 passengers/5min  
- **School Zone (Dismissal)**: λ = 12.0 → 8-16 passengers/5min
- **Rural Area (Off-Peak)**: λ = 0.5 → 0-2 passengers/5min

---

## 🚌 **Route Assignment Logic**

### **Proximity-Based Matching**

1. **Find Nearest Route**: Calculate distance from spawn zone to all routes
2. **Distance Threshold**: Routes within 2km of zone center
3. **Route Selection**: Choose closest route with active service
4. **Destination Assignment**: Generate realistic destination along route

### **Trip Purpose Logic**

```python
# Morning from residential → Commercial destinations
# Evening from commercial → Residential destinations  
# School hours → Education-related trips
# Shopping hours → Retail/amenities destinations
```

---

## 📈 **Statistical Validation**

### **Poisson Distribution Characteristics**

- **Mean ≈ Variance**: For Poisson, σ² ≈ λ
- **Natural Randomness**: No artificial patterns
- **Scalable**: Works for any population density
- **Time-Responsive**: Adapts to different periods

### **Quality Metrics**

- **Geographic Distribution**: Spawns spread across actual population zones
- **Temporal Patterns**: Higher spawns during actual peak hours
- **Route Coverage**: All routes receive appropriate passenger loads
- **Trip Realism**: Purposes match zone types and times

---

## 🚀 **Usage Examples**

### **Basic Poisson Spawning**

```python
async def spawn_passengers():
    async with StrapiApiClient() as client:
        spawner = PoissonGeoJSONSpawner(client)
        await spawner.initialize("barbados")
        
        current_time = datetime.now()
        requests = await spawner.generate_poisson_spawn_requests(
            current_time, time_window_minutes=5
        )
        
        print(f"Generated {len(requests)} statistically-distributed passengers")
```

### **Time-Based Analysis**

```python
# Test different times of day
for hour in [8, 12, 17, 22]:  # Rush, lunch, evening, night
    test_time = datetime.now().replace(hour=hour)
    requests = await spawner.generate_poisson_spawn_requests(test_time)
    print(f"{hour}:00 - {len(requests)} passengers")
```

---

## ✅ **Key Advantages**

### **Realistic Patterns**

- ✅ **Statistical Accuracy**: Poisson distribution matches real passenger arrivals
- ✅ **Geographic Realism**: Based on actual population and land use data
- ✅ **Time Sensitivity**: Different patterns for rush hour vs off-peak
- ✅ **Zone Diversity**: Residential, commercial, amenity-specific patterns

### **Data-Driven Approach**

- ✅ **GeoJSON Integration**: Uses real geographic boundary data
- ✅ **Population-Based**: Spawn rates proportional to actual population density
- ✅ **Activity Centers**: Higher spawns near schools, shopping, offices
- ✅ **Transport Hubs**: Bus stops and transit centers included

### **System Integration**

- ✅ **API Compatibility**: Works with existing StrapiApiClient
- ✅ **Route Integration**: Automatic assignment to nearest routes
- ✅ **Scalable Architecture**: Easy to add new countries/regions
- ✅ **Statistical Validation**: Built-in distribution testing

---

## 🎯 **Next Steps**

1. **Test with Real Data**: Run `test_poisson_geojson_spawning.py`
2. **Validate Statistics**: Confirm Poisson distribution characteristics
3. **Geographic Accuracy**: Verify spawns match population patterns
4. **Integration Testing**: Connect with vehicle simulation system
5. **Performance Optimization**: Optimize GeoJSON processing for larger datasets

This system provides **statistically accurate, geographically realistic passenger spawning** using established mathematical models and real-world data! 🎲🗺️
