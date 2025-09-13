"""
QGIS Python Script: Extract All Location Types at Once
Run this in QGIS Python Console to get all location data in one operation
"""

# QGIS Python Console Script - Copy and paste this entire script
import processing

# Define your study area bounding box (adjust coordinates for your Route 1 area)
# Format: 'left,right,bottom,top' in decimal degrees
# Example for Barbados Route 1 area:
bbox = '-59.65,-59.61,13.10,13.29'  # Adjust these coordinates!

# Output file path - change this to your desired location
output_file = 'C:/temp/barbados_all_locations.geojson'

print("🌍 Extracting ALL location types from OpenStreetMap...")
print(f"📍 Study area: {bbox}")
print(f"💾 Output file: {output_file}")

# Single comprehensive query to get everything at once
try:
    result = processing.run("quickosm:buildqueryextent", {
        'KEY': 'amenity|shop|office|leisure|tourism|building|place',
        'VALUE': '',  # Empty = get all values
        'EXTENT': bbox,
        'OUTPUT': output_file
    })
    
    # Count features
    layer = result['OUTPUT_POINTS']
    feature_count = layer.featureCount()
    
    print(f"✅ SUCCESS! Extracted {feature_count} locations")
    print(f"📂 File saved: {output_file}")
    print(f"🗺️  Layer added to map: {layer.name()}")
    
    # Show breakdown by type
    print("\n📊 Location type breakdown:")
    
    # Get unique values from relevant fields
    type_counts = {}
    
    for feature in layer.getFeatures():
        attrs = feature.attributes()
        field_names = [field.name() for field in layer.fields()]
        
        # Check each attribute for location type info
        for i, field_name in enumerate(field_names):
            if field_name in ['amenity', 'shop', 'office', 'leisure', 'tourism', 'building', 'place']:
                value = attrs[i]
                if value and str(value).strip():  # Not null/empty
                    key = f"{field_name}={value}"
                    type_counts[key] = type_counts.get(key, 0) + 1
    
    # Show top 20 most common types
    for location_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"   {location_type}: {count} locations")
    
    if len(type_counts) > 20:
        print(f"   ... and {len(type_counts) - 20} more types")

except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    print("\n🔧 Troubleshooting tips:")
    print("1. Make sure QuickOSM plugin is installed")
    print("2. Check your bounding box coordinates")
    print("3. Ensure output directory exists")
    print("4. Try a smaller study area if query times out")

print("\n🎯 Next steps:")
print("1. Review the extracted data on the map")
print("2. Clean/filter unwanted location types if needed")
print("3. Use this GeoJSON file in your passenger simulation!")