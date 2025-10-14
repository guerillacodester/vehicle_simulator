#!/usr/bin/env python3
"""
Quick script to check highway count in database
"""

import requests

STRAPI_URL = "http://localhost:1337"
API_URL = f"{STRAPI_URL}/api"
API_TOKEN = "b127418caf99e995d561f1c787005e328c8b9168e7fcc313460e43e032259a2b26d209b260b1dd8c0ca5dced2f20db90823984a50e2ec7429070552acad2b81f94bcad87ddf09e3314ded62538163e55e7f11a8909de45f67dd95890311211f5c1af76b86452a9e4f585ea9e4d3832e434c6cb46b97823c103801323a0214442"

# Check total highways (no country filter)
response = requests.get(
    f"{API_URL}/highways",
    params={"pagination[pageSize]": 1},
    headers={"Authorization": f"Bearer {API_TOKEN}"}
)

if response.status_code == 200:
    total = response.json()["meta"]["pagination"]["total"]
    print(f"Total highways in database: {total}")
else:
    print(f"Failed to fetch highways: {response.status_code}")

# Check highway-shapes
response = requests.get(
    f"{API_URL}/highway-shapes",
    params={"pagination[pageSize]": 1},
    headers={"Authorization": f"Bearer {API_TOKEN}"}
)

if response.status_code == 200:
    total = response.json()["meta"]["pagination"]["total"]
    print(f"Total highway-shapes in database: {total}")
else:
    print(f"Failed to fetch shapes: {response.status_code}")

# Check with Barbados filter
response = requests.get(
    f"{API_URL}/countries",
    params={"filters[code][$eq]": "BB"},
    headers={"Authorization": f"Bearer {API_TOKEN}"}
)

if response.status_code == 200:
    country_id = response.json()["data"][0]["documentId"]
    
    response = requests.get(
        f"{API_URL}/highways",
        params={
            "filters[country][documentId][$eq]": country_id,
            "pagination[pageSize]": 1
        },
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    if response.status_code == 200:
        total = response.json()["meta"]["pagination"]["total"]
        print(f"Highways for Barbados (filter by documentId): {total}")
