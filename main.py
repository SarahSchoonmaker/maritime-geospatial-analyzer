import pandas as pd
from sqlalchemy.types import Float, String, DateTime
from tqdm import tqdm
from src.db import engine
import subprocess
import os
import sys

def clean_chunk(chunk):
    # Rename to match internal schema
    chunk.rename(columns={
        "MMSI": "imo_number",
        "BaseDateTime": "timestamp",
        "LAT": "latitude",
        "LON": "longitude",
        "SOG": "speed_kn",
        "VesselName": "name",
        "Status": "status"
    }, inplace=True)

    chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], errors="coerce")
    chunk.dropna(subset=["latitude", "longitude", "timestamp"], inplace=True)

    return chunk[[
        "imo_number", "name", "timestamp",
        "latitude", "longitude", "speed_kn", "status"
    ]]

def main():
    csv_path = "data/vessels.csv"
    chunk_size = 100_000
    max_chunks = 2

    print("🚢 Starting partial import for development...")

    reader = pd.read_csv(csv_path, chunksize=chunk_size)

    for i, chunk in tqdm(enumerate(reader), desc="Processing chunks"):
        if i >= max_chunks:
            break

        cleaned = clean_chunk(chunk)

        cleaned.to_sql(
            "vessels",
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

    print("✅ Partial data load complete.")
    print("🚀 Launching Streamlit dashboard...")

    try:
        # Run streamlit in detached mode so Ctrl+C doesn’t hang
        if sys.platform == "win32":
            subprocess.Popen(["streamlit", "run", "app.py"],
                             creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            subprocess.Popen(["streamlit", "run", "app.py"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             preexec_fn=os.setpgrp)
    except Exception as e:
        print("❌ Failed to launch Streamlit:", e)

if __name__ == "__main__":
    main()
    print("✅ Run complete. Now launch Streamlit with `streamlit run app.py`.")
