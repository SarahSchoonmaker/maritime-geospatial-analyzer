import os
import pandas as pd
from tqdm import tqdm
from sqlalchemy.types import Float, String, DateTime
from src.db import engine

CSV_PATH = "data/vessels.csv"
CHUNK_SIZE = 100_000
MAX_CHUNKS = 2
TABLE_NAME = "vessels"

COLUMN_MAP = {
    "MMSI": "imo_number",
    "BaseDateTime": "timestamp",
    "LAT": "latitude",
    "LON": "longitude",
    "SOG": "speed_kn",
    "VesselName": "name",
    "Status": "status"
}

def clean_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk.rename(columns=COLUMN_MAP, inplace=True)
    chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], errors="coerce")
    chunk.dropna(subset=["latitude", "longitude", "timestamp"], inplace=True)
    return chunk[["imo_number", "name", "timestamp", "latitude", "longitude", "speed_kn", "status"]]

def load_data_from_csv():
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV not found at {CSV_PATH}")
        return

    print("🚢 Loading CSV data into database...")
    reader = pd.read_csv(CSV_PATH, chunksize=CHUNK_SIZE)

    for i, chunk in tqdm(enumerate(reader), desc="Processing chunks"):
        if i >= MAX_CHUNKS:
            break

        cleaned = clean_chunk(chunk)
        cleaned.to_sql(
            TABLE_NAME,
            engine,
            if_exists="append" if i > 0 else "replace",
            index=False,
            dtype={
                "imo_number": String,
                "name": String,
                "timestamp": DateTime,
                "latitude": Float,
                "longitude": Float,
                "speed_kn": Float,
                "status": String
            }
        )
        print(f"✔️ Inserted chunk {i+1} with {len(cleaned)} rows")

    print("✅ Data loaded into database.")

if __name__ == "__main__":
    load_data_from_csv()
