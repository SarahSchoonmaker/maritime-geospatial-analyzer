from math import radians, cos, sin, asin, sqrt
import pandas as pd

# Define key ports with lat/lon
PORTS = [
    {"name": "Port of Los Angeles", "lat": 33.738, "lon": -118.272},
    {"name": "Port of New York", "lat": 40.668, "lon": -74.045},
    {"name": "Port of Houston", "lat": 29.730, "lon": -95.265},
    {"name": "Port of Miami", "lat": 25.778, "lon": -80.179},
    {"name": "Port of Seattle", "lat": 47.60, "lon": -122.34},
    {"name": "Port of Savannah", "lat": 32.08, "lon": -81.10}
]

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two (lat, lon) points in kilometers.
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 6371 * 2 * asin(sqrt(a))

def analyze_port_congestion(vessels_df, radius_km=10):
    """
    Return a summary of total vessel counts within a radius around known ports.
    """
    summary = []

    for port in PORTS:
        distances = vessels_df.apply(
            lambda row: haversine(row["latitude"], row["longitude"], port["lat"], port["lon"]),
            axis=1
        )
        count = distances[distances <= radius_km].count()

        summary.append({
            "port": port["name"],
            "vessel_count": count
        })

    return pd.DataFrame(summary)

def analyze_congestion_by_type(vessels_df, radius_km=10):
    """
    Return detailed vessel counts by port and status (e.g., anchored, moored).
    """
    congestion = []

    for port in PORTS:
        distances = vessels_df.apply(
            lambda row: haversine(row["latitude"], row["longitude"], port["lat"], port["lon"]),
            axis=1
        )
        nearby = vessels_df[distances <= radius_km]

        grouped = nearby.groupby("status").size().reset_index(name="count")
        for _, row in grouped.iterrows():
            congestion.append({
                "port": port["name"],
                "vessel_status": row["status"],
                "count": row["count"],
                "lat": port["lat"],
                "lon": port["lon"]
            })

    return pd.DataFrame(congestion)
