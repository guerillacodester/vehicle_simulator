import math

# Route 1 coordinates from Strapi DB
coords = [
    [-59.61552132051129, 13.326607060339862],
    [-59.6156721, 13.3264114],
    [-59.6159291, 13.3259475],
    [-59.6161146, 13.325635],
    [-59.6163443, 13.3252255],
    [-59.6164124, 13.3251286],
    [-59.6167544, 13.3245466],
    [-59.6171044, 13.3239372],
    [-59.6172778, 13.3235481],
    [-59.6176022, 13.3229333],
    [-59.6178103, 13.3226254],
    [-59.6179741, 13.3223862],
    [-59.6180066, 13.3223388],
    [-59.618411, 13.3219112],
    [-59.6187893, 13.3216074],
    [-59.6191824, 13.3213449],
    [-59.6194709, 13.321105],
    [-59.6202109, 13.3205495],
    [-59.6208474, 13.3201252],
    [-59.6215653, 13.3196702],
    [-59.6220374, 13.3193094],
    [-59.62291, 13.3184526],
    [-59.623207, 13.3181959],
    [-59.6233277, 13.3180918],
    [-59.6234396, 13.3179816],
    [-59.623472629021435, 13.3179604303923]
]

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

total_km = 0.0
for i in range(len(coords)-1):
    lon1, lat1 = coords[i]
    lon2, lat2 = coords[i+1]
    total_km += haversine(lon1, lat1, lon2, lat2)

print(f"Total route 1 distance (Strapi DB points): {total_km:.3f} km")
