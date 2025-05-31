import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import FastMarkerCluster
from sqlalchemy import create_engine
from datetime import datetime
from src.congestion_analysis import analyze_congestion_by_type

# Connect to SQLite DB
engine = create_engine("sqlite:///db/vessels.db")

# Page setup
st.set_page_config(page_title="Maritime Analyzer", layout="wide")
st.title("\U0001f6a3 Maritime Trade Route Risk Analyzer")
st.markdown("This dashboard shows vessel positions and port congestion based on AIS data.")

# Sidebar controls
st.sidebar.header("\U0001f50d Filters")
max_rows = st.sidebar.slider("Max rows to load", 1000, 50000, 5000, step=1000)
radius_km = st.sidebar.slider("Port radius (km)", 5, 100, 20, step=5)

# Load data
@st.cache_data(show_spinner=True)
def load_data(n):
    query = f"""
        SELECT latitude, longitude, name, status, timestamp, speed_kn, imo_number
        FROM vessels
        LIMIT {n}
    """
    return pd.read_sql(query, engine)

df = load_data(max_rows)

status_labels = {
    0: "Underway using engine",
    1: "At anchor",
    2: "Not under command",
    3: "Restricted maneuverability",
    4: "Constrained by draft",
    5: "Moored",
    6: "Aground",
    7: "Engaged in fishing",
    8: "Under sail",
    9: "Reserved for future use",
    10: "Reserved for future use",
    11: "Reserved for future use",
    12: "Reserved for future use",
    13: "Reserved for future use",
    14: "AIS-SART / MOB / EPIRB",
    15: "Unknown or undefined"
}

# Determine status options from data
all_statuses = sorted([s for s in df["status"].dropna().unique().tolist() if s in status_labels])
default_statuses = [s for s in all_statuses if s != 15]  # Don't pre-select status 15

selected_statuses = st.sidebar.multiselect(
    "Select status codes to show",
    options=all_statuses,
    default=default_statuses
)

# Optional: show current status counts
with st.sidebar.expander("🛟 Vessel Status Codes"):
    for code in all_statuses:
        st.markdown(f"- `{code}`: {status_labels.get(code, 'Other')}")

# Filter data
df = df[df["status"].isin(selected_statuses)]

# Metrics summary
st.markdown("### \U0001f4ca Dataset Overview")
cols = st.columns(4)
cols[0].metric("\U0001f4e6 Total AIS Records", len(df))
cols[1].metric("\U0001f6a2 Unique Vessels", df["imo_number"].nunique())
cols[2].metric("\u2693 Active Status Types", df["status"].nunique())
cols[3].metric("\U0001f4cd Port Radius (km)", radius_km)

# Vessel positions map
st.markdown("## \U0001f30d Vessel Positions Map")
if df.empty:
    st.warning("No vessel data available. Try loading more rows or adjusting status filter.")
else:
    m = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=4)
    coords = list(zip(df["latitude"], df["longitude"]))
    FastMarkerCluster(coords).add_to(m)
    st_folium(m, width=1200, height=500)

# Port congestion heatmap
st.markdown("## \U0001f525 Port Congestion Heatmap")
st.markdown(f"""
This heatmap shows how many vessels are within a **{radius_km} km** radius of major U.S. ports.

- 🟥 Each red circle represents a port.
- 📏 The **circle size** is scaled to the number of nearby vessels.
- ⚪ A light gray transparent ring marks the scanning radius.
""")

try:
    congestion_data = analyze_congestion_by_type(df, radius_km=radius_km)
    if congestion_data.empty:
        st.info("No congestion detected. Try increasing radius or loading more rows.")
    else:
        heatmap = folium.Map(location=[39, -95], zoom_start=4)

        for port in congestion_data["port"].unique():
            port_df = congestion_data[congestion_data["port"] == port]
            total = int(port_df["count"].sum())
            port_lat = float(port_df["lat"].iloc[0])
            port_lon = float(port_df["lon"].iloc[0])

            # Radius ring
            folium.Circle(
                radius=radius_km * 1000,
                location=(port_lat, port_lon),
                color="#999",
                fill=True,
                fill_opacity=0.05,
                weight=1,
            ).add_to(heatmap)

            # Congestion visual
            folium.Circle(
                radius=total * 500,
                location=(port_lat, port_lon),
                popup=(
                    f"<b>{port}</b><br>"
                    f"{total} vessels within {radius_km} km"
                ),
                color="crimson",
                fill=True,
                fill_opacity=0.6,
            ).add_to(heatmap)

        st_folium(heatmap, width=1200, height=600)

except Exception as e:
    st.error(f"❌ Error rendering congestion heatmap: {e}")

# Footer
st.markdown("---")
st.markdown(f"📅 *Dashboard last updated:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
