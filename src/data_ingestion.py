import pandas as pd

def load_vessel_data(source="csv", path_or_url="data/vessels.csv"):
    df = pd.read_csv(path_or_url)

    df.rename(columns={
        "MMSI": "imo_number",
        "BaseDateTime": "timestamp",
        "LAT": "latitude",
        "LON": "longitude",
        "SOG": "speed_kn",
        "VesselName": "name",
        "Status": "status"
    }, inplace=True)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    df.dropna(subset=["latitude", "longitude", "timestamp"], inplace=True)

    return df[[
        "imo_number", "name", "timestamp", "latitude",
        "longitude", "speed_kn", "status"
    ]]
