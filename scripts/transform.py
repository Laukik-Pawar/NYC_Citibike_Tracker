import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text

# Database connection parameters (Internal Docker Network)
DB_USER = "admin"
DB_PASSWORD = "password123"
DB_HOST = "postgres"
DB_PORT = "5432"
DB_NAME = "bikeshare"

def get_engine():
    """Establish connection to PostgreSQL for Pandas."""
    return create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def transform_data():
    engine = get_engine()
    
    with engine.begin() as conn:
        # 1. Create a High-Water Mark table to track what we've already processed
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS etl_watermark (
                table_name VARCHAR(50) PRIMARY KEY,
                last_processed_id INT
            );
        """))
        
        # 2. Get the ID of the last row we transformed
        result = conn.execute(text("SELECT last_processed_id FROM etl_watermark WHERE table_name = 'raw_station_status'")).fetchone()
        last_id = result[0] if result else 0

    print(f"Extracting new records starting after ID: {last_id}")

    # 3. Fetch ONLY new data, using a LATERAL JOIN for closest-in-time weather matching
    query = f"""
        SELECT 
            r.id as raw_id,
            r.station_id,
            r.num_bikes_available as bikes_available,
            r.last_reported as recorded_at,
            EXTRACT(HOUR FROM r.last_reported) as hour_of_day,
            EXTRACT(DOW FROM r.last_reported) as day_of_week,
            w.temperature_celsius
        FROM raw_station_status r
        -- LATERAL JOIN finds the exact closest weather record in time for EACH station reading
        LEFT JOIN LATERAL (
            SELECT temperature_celsius
            FROM weather_data w
            ORDER BY ABS(EXTRACT(EPOCH FROM (r.last_reported - w.recorded_at))) ASC
            LIMIT 1
        ) w ON true
        WHERE r.id > {last_id}
          AND r.is_renting = TRUE
          AND r.last_reported > '2020-01-01' -- Ghost data filter
        ORDER BY r.id ASC
    """
    
    df = pd.read_sql(query, engine)
    
    if df.empty:
        print("No new records to process.")
        return

    # 4. Format features for the ML Model
    df['is_weekend'] = df['day_of_week'].isin([0, 6])
    df['day_of_week'] = df['day_of_week'].astype(int)
    df['hour_of_day'] = df['hour_of_day'].astype(int)
    
    # Grab the highest ID from this batch to update our watermark
    max_processed_id = int(df['raw_id'].max())
    
    # Drop the raw_id as it doesn't belong in the feature table
    features_df = df.drop(columns=['raw_id'])
    
    # 5. Load into ml_feature_table
    features_df.to_sql('ml_feature_table', engine, if_exists='append', index=False)
    print(f"Successfully loaded {len(features_df)} transformed records into ml_feature_table.")
    
    # 6. Update the watermark so the next 5-minute run knows where to start
    with engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO etl_watermark (table_name, last_processed_id)
            VALUES ('raw_station_status', {max_processed_id})
            ON CONFLICT (table_name) DO UPDATE 
            SET last_processed_id = {max_processed_id};
        """))
    print(f"Updated watermark: last_processed_id = {max_processed_id}")

if __name__ == "__main__":
    print("Starting ETL Transformation Process...")
    transform_data()
    print("Transformation Complete!")