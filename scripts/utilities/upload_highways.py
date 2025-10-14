"""
Upload barbados_highway.json to Strapi via the GeoJSON upload endpoint
"""
import requests
import json

# Configuration
STRAPI_URL = "http://localhost:1337"
GEOJSON_FILE_PATH = "commuter_service/geojson_data/barbados_highway.json"
COUNTRY_ID = 1  # Barbados country ID

def upload_highways():
    """Upload highways GeoJSON to Strapi"""
    
    # Read the GeoJSON file
    print(f"Reading {GEOJSON_FILE_PATH}...")
    with open(GEOJSON_FILE_PATH, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    print(f"Found {len(geojson_data['features'])} highway features")
    
    # Prepare the upload
    url = f"{STRAPI_URL}/api/countries/upload-geojson"
    
    # Open file in binary mode for upload
    with open(GEOJSON_FILE_PATH, 'rb') as f:
        files = {
            'geojson': ('barbados_highway.json', f, 'application/json')
        }
        
        data = {
            'countryId': COUNTRY_ID,
            'fileType': 'highways'
        }
        
        print(f"\nUploading to {url}...")
        print(f"Country ID: {COUNTRY_ID}")
        print(f"File type: highways")
        
        response = requests.post(url, files=files, data=data)
    
    # Check response
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Upload successful!")
        print(f"Features uploaded: {result.get('features', 'unknown')}")
        print(f"File ID: {result.get('file', {}).get('id', 'unknown')}")
        print("\nStrapi will now process the highways in the background...")
        print("Check the Strapi console for processing logs")
    else:
        print(f"\n❌ Upload failed with status {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == '__main__':
    upload_highways()
