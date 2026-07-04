import requests
import psycopg2
from datetime import datetime

# Database connection parameters (Matching our Docker setup)
DB_USER = "admin"
DB_PASSWORD = "password123"
DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "bikeshare"

# Free Public API Endpoints
CITI_BIKE_URL = "https://gbfs.citibikenyc.com/gbfs/en/station_status.json"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&current_weather=true"

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

def fetch_and_load_weather(conn):
    print("Fetching live weather data for NYC...")
    response = requests.get(WEATHER_URL).json()
    current = response['current_weather']
    
    cursor = conn.cursor()
    # Insert the parsed JSON into our SQL table
    cursor.execute("""
        INSERT INTO weather_data (temperature_celsius, wind_speed_kmh, recorded_at)
        VALUES (%s, %s, %s)
    """, (current['temperature'], current['windspeed'], datetime.now()))
    
    conn.commit()
    cursor.close()
    print("Weather data successfully loaded!")

# def fetch_and_load_bikes(conn):
#     print("Fetching live Citi Bike station statuses...")
#     response = requests.get(CITI_BIKE_URL).json()
#     stations = response['data']['stations']
    
#     cursor = conn.cursor()
#     # We will insert the first 100 stations to keep the local database fast and light
#     for station in stations[:100]:
#         cursor.execute("""
#             INSERT INTO raw_station_status 
#             (station_id, num_bikes_available, num_docks_available, is_renting, last_reported)
#             VALUES (%s, %s, %s, %s, %s)
#         """, (
#             station['station_id'],
#             station['num_bikes_available'],
#             station['num_docks_available'],
#             station['is_renting'] == 1,
#             datetime.fromtimestamp(station['last_reported'])
#         ))
        
#     conn.commit()
#     cursor.close()
#     print("Bike station data successfully loaded!")
def fetch_and_load_bikes(conn):
    print("Fetching live Citi Bike station statuses...")
    response = requests.get(CITI_BIKE_URL).json()
    stations = response['data']['stations']
    
    cursor = conn.cursor()
    # We will insert the first 100 stations to keep the local database fast and light
    for station in stations[:100]:
        try:
            cursor.execute("""
                INSERT INTO raw_station_status 
                (station_id, num_bikes_available, num_docks_available, is_renting, last_reported)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                station['station_id'],
                station['num_bikes_available'],
                station['num_docks_available'],
                station['is_renting'] == 1,
                datetime.fromtimestamp(station['last_reported'])
            ))
            conn.commit() # Commit incrementally so valid rows are saved immediately
        except Exception as e:
            print(f"Skipping bad record for station {station.get('station_id', 'Unknown')}: {e}")
            conn.rollback() # Clear the aborted transaction state so the loop can continue safely
            
    cursor.close()
    print("Bike station data successfully loaded!")

if __name__ == "__main__":
    print("Starting ETL Ingestion Process...")
    conn = get_db_connection()
    try:
        fetch_and_load_weather(conn)
        fetch_and_load_bikes(conn)
        print("Phase 2 Complete! The database has been updated.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
        print("Database connection closed.")