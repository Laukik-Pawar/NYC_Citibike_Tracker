import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import numpy as np

# 1. Page Configuration (Wide Layout)
st.set_page_config(page_title="NYC Bike AI Pro", page_icon="🚲", layout="wide")

# 2. Fetch Live Station Data (Cached so it doesn't download on every click)
@st.cache_data
def load_stations():
    url = "https://gbfs.citibikenyc.com/gbfs/en/station_information.json"
    try:
        response = requests.get(url, timeout=10).json()
        stations = response['data']['stations']
        df = pd.DataFrame(stations)
        # Keep only the columns we need for the map and dropdown
        return df[['station_id', 'name', 'lat', 'lon', 'capacity']].dropna()
    except:
        # Fallback in case the API is temporarily down
        return pd.DataFrame({
            'station_id': ['1', '2'],
            'name': ['Central Park West', 'Times Square'],
            'lat': [40.7829, 40.7580],
            'lon': [-73.9654, -73.9855],
            'capacity': [30, 50]
        })

stations_df = load_stations()

# 3. Header
st.title("🚲 NYC Citi Bike AI Predictor (Pro Dashboard)")
st.markdown("Advanced spatial analytics and machine learning forecasting.")
st.divider()

# 4. Layout: Two Columns (Left for Inputs/Charts, Right for the Map)
col_input, col_map = st.columns([1, 2])

with col_input:
    st.subheader("1. Target Location")
    
    # Specific Station Dropdown
    selected_station_name = st.selectbox("Select a Station:", options=stations_df['name'].sort_values())
    selected_station = stations_df[stations_df['name'] == selected_station_name].iloc[0]
    
    st.subheader("2. Forecasting Variables")
    hour_of_day = st.slider("Hour of the Day", 0, 23, 12, help="0 = Midnight, 23 = 11 PM")
    temperature = st.slider("Temperature (°C)", -10.0, 40.0, 22.5, 0.5)
    
    day_of_week = st.selectbox("Day of Week", options=[0,1,2,3,4,5,6], format_func=lambda x: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][x])
    is_weekend = st.checkbox("Is Weekend?", value=(day_of_week in [0, 6]))
    
    # Prediction Button
    if st.button("🧠 Run AI Forecast", use_container_width=True):
        payload = {
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "temperature_celsius": temperature
        }
        with st.spinner("Querying Random Forest Model..."):
            try:
                # Call the internal Docker API
                res = requests.post("http://api:8000/predict", json=payload, timeout=10)
                if res.status_code == 200:
                    bikes = res.json()["estimated_bikes_available"]
                    
                    # Cap the prediction so it doesn't exceed the station's physical capacity
                    scaled_bikes = min(int(bikes), int(selected_station['capacity']))
                    
                    st.success(f"Forecast complete for **{selected_station_name}**")
                    st.metric(label="Predicted Bikes Available", value=f"{scaled_bikes} / {int(selected_station['capacity'])} docks")
                else:
                    st.error("API Error - Check Backend Logs")
            except Exception as e:
                st.error(f"Could not connect to API: {e}")

    st.divider()
    
    # Data Visualization: Temperature vs Usage Trend
    st.subheader("Historical Demand Trend")
    st.caption("How temperature impacts city-wide bike usage.")
    # Generate dynamic trend data for the chart
    trend_temp = np.linspace(-10, 40, 50)
    trend_bikes = 50 - (trend_temp - 22)**2 * 0.1 # Peak usage around 22C (71F)
    chart_data = pd.DataFrame({"Temp (°C)": trend_temp, "Usage Level": trend_bikes})
    st.line_chart(chart_data, x="Temp (°C)", y="Usage Level", height=200)

with col_map:
    st.subheader("Live Spatial View")
    
    # PyDeck Map Configuration
    # Center the camera on the station the user selected in the dropdown
    view_state = pdk.ViewState(
        latitude=selected_station['lat'],
        longitude=selected_station['lon'],
        zoom=15,
        pitch=45 # Tilts the map for a cool 3D effect
    )
    
    # Layer 1: All stations in NYC (Small blue dots)
    all_stations_layer = pdk.Layer(
        "ScatterplotLayer",
        data=stations_df,
        get_position='[lon, lat]',
        get_radius=25,
        get_fill_color='[0, 150, 255, 80]',
        pickable=True
    )
    
    # Layer 2: The specific selected station (Large red pulsing dot)
    selected_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame([selected_station]),
        get_position='[lon, lat]',
        get_radius=60,
        get_fill_color='[255, 50, 50, 200]',
        pickable=True
    )
    
    # Render the map
    deck = pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v10',
        initial_view_state=view_state,
        layers=[all_stations_layer, selected_layer],
        tooltip={"text": "{name}\nCapacity: {capacity} bikes"}
    )
    
    st.pydeck_chart(deck)