CREATE TABLE IF NOT EXISTS raw_station_status (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(50) NOT NULL,
    num_bikes_available INT,
    num_docks_available INT,
    is_renting BOOLEAN,
    last_reported TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    temperature_celsius NUMERIC(5, 2),
    precipitation_mm NUMERIC(5, 2),
    wind_speed_kmh NUMERIC(5, 2),
    recorded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ml_feature_table (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(50),
    hour_of_day INT,
    day_of_week INT,
    is_weekend BOOLEAN,
    temperature_celsius NUMERIC(5, 2),
    bikes_available INT,
    recorded_at TIMESTAMP
);