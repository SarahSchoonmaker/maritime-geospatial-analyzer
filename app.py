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
st.set_page_config(
    page_title="Maritime Analyzer",
    layout="wide"
)

# Lightweight mobile-friendly CSS
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; }
        .stMarkdown p, .stMetric { font-size: 0.95rem !important; }
        @media (max-width: 768px) {
            .stSlider label, .stMultiSelect label, .stSelectbox label {
                font-size: 0.85rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.title("🚢 Maritime Trade Route Risk Analyzer")
st.markdown("This dashboard shows vessel positions and port congestion based on AIS data.")

# Sidebar filters
st.sidebar.header("🔎 Filters")
max_rows = st.sidebar.slider("Max rows to load", 1000, 50000, 5000, step=1000)
radius_km = st.sidebar.slider("Port radius (km)", 5, 100, 20, step=5)

# Load data from DB
@st.cache_data(show_spinner=True)
def load_data(n):
    query = f"""
        SELECT latitude, longitude, name, status, timestamp, speed_kn, imo_number
        FROM vessels
        LIMIT {n}
    """
    df = pd.read_sql(query, engine)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["status"] = pd.to_numeric(df["status"], errors="coerce").astype("Int64")
    df.dropna(subset=["latitude", "longitude", "timestamp"], inplace=True)
    return df

df = load_data(max_rows)

# Status code mappings
status_labels = {
    0: "Underway using engine", 1: "At anchor", 2: "Not under command",
    3: "Restricted maneuverability", 4: "Constrained by draft", 5: "Moored",
    6: "Aground", 7: "Engaged in fishing", 8: "Under sail",
    9: "Reserved for future use", 10: "Reserved for future use",
    11: "Reserved for future use", 12: "Reserved for future use",
    13: "Reserved for future use", 14: "AIS-SART / MOB / EPIRB",
    15: "Unknown or undefined"
}

# Filter by vessel status
all_statuses = sorted([int(s) for s in df["status"].dropna().unique() if s in status_labels])
default_statuses = [s for s in all_statuses if s != 15]

selected_statuses = st.sidebar.multiselect(
    "Select vessel status codes to display:",
    options=all_statuses,
    default=default_statuses
)

with st.sidebar.expander("🛟 Vessel Status Legend"):
    for code in all_statuses:
        st.markdown(f"- `{code}`: {status_labels.get(code, 'Unknown')}")

# Apply status filter
df = df[df["status"].isin(selected_statuses)]

# Summary metrics
st.markdown("### 📊 Dataset Overview")
cols = st.columns(2)
cols[0].metric("📦 Total AIS Records", len(df))
cols[1].metric("🚢 Unique Vessels", df["imo_number"].nunique())

cols = st.columns(2)
cols[0].metric("⚓ Active Status Types", df["status"].nunique())
cols[1].metric("📍 Port Radius (km)", radius_km)

# Vessel Position Map
st.markdown("## 🌍 Vessel Positions Map")
if df.empty:
    st.warning("No vessel data available. Try adjusting filters or loading more rows.")
else:
    map_center = [df["latitude"].mean(), df["longitude"].mean()]
    m = folium.Map(location=map_center, zoom_start=4)
    coords = list(zip(df["latitude"], df["longitude"]))
    FastMarkerCluster(coords).add_to(m)
    st_folium(m, width="100%", height=400)

# Congestion Heatmap
st.markdown("## 🔥 Port Congestion Heatmap")
st.markdown(f"""
Shows how many vessels are within a **{radius_km} km** radius of major U.S. ports.

- 🟥 Each red circle = port  
- 📏 Circle size = number of nearby vessels  
- ⚪ Light gray ring = scan radius  
""")

try:
    congestion_data = analyze_congestion_by_type(df, radius_km=radius_km)
    if congestion_data.empty:
        st.info("No congestion detected. Increase radius or load more rows.")
    else:
        heatmap = folium.Map(location=[39, -95], zoom_start=4)
        for port in congestion_data["port"].unique():
            port_df = congestion_data[congestion_data["port"] == port]
            total = int(port_df["count"].sum())
            port_lat = float(port_df["lat"].iloc[0])
            port_lon = float(port_df["lon"].iloc[0])
            folium.Circle(
                radius=radius_km * 1000, location=(port_lat, port_lon),
                color="#999", fill=True, fill_opacity=0.05, weight=1,
            ).add_to(heatmap)
            folium.Circle(
                radius=total * 500, location=(port_lat, port_lon),
                popup=f"<b>{port}</b><br>{total} vessels",
                color="crimson", fill=True, fill_opacity=0.6,
            ).add_to(heatmap)
        st_folium(heatmap, width="100%", height=500)
except Exception as e:
    st.error(f"❌ Error rendering congestion heatmap: {e}")

# Footer
st.markdown("---")
st.markdown(f"📅 *Dashboard last updated:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
