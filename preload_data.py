import os
import logging
import pandas as pd
from tqdm import tqdm
from sqlalchemy.types import Float, String, DateTime
from src.db import engine

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

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

def load_data_from_csv() -> bool:
    if not os.path.exists(CSV_PATH):
        logging.warning(f"❌ CSV file not found: {CSV_PATH}")
        return False

    logging.info("🚢 Importing CSV into database...")
    reader = pd.read_csv(CSV_PATH, chunksize=CHUNK_SIZE)

    for i, chunk in tqdm(enumerate(reader), desc="Processing chunks"):
        if i >= MAX_CHUNKS:
            break

        cleaned = clean_chunk(chunk)
        with engine.begin() as conn:
            cleaned.to_sql(
                TABLE_NAME,
                con=conn,
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
        logging.info(f"✔️ Inserted chunk {i+1} with {len(cleaned)} rows")

    logging.info("✅ CSV load complete.")
    return True

if __name__ == "__main__":
    if load_data_from_csv():
        logging.info("✅ Data load complete. Now run: streamlit run app.py")
    else:
        logging.warning("⚠️ Skipped loading CSV because file was missing.")
