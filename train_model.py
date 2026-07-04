import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error
import joblib

def main():
    print("=== Phase 4: Machine Learning Training ===")
    
    # 1. Connect to the Database
    # We use the internal Docker hostname (postgres) and port (5432)
    print("Connecting to the database...")
    db_uri = 'postgresql+psycopg2://admin:password123@postgres:5432/bikeshare'
    engine = create_engine(db_uri)

    # 2. Extract the Clean Data
    print("Pulling clean data from ml_feature_table...")
    query = "SELECT * FROM ml_feature_table"
    df = pd.read_sql(query, engine)

    # Safety check
    if len(df) < 10:
        print("Not enough data to train! Let Airflow run a few more times to build up the dataset.")
        return

    print(f"Successfully loaded {len(df)} rows of training data.")

    # 3. Define Features (X) and Target (y)
    # The model learns from these features:
    X = df[['hour_of_day', 'day_of_week', 'is_weekend', 'temperature_celsius']]
    # The model tries to predict this target:
    y = df['bikes_available']

    # Split the data: 80% for training, 20% for testing the model's accuracy
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train and Compare Multiple Machine Learning Models
    print("\nTraining and comparing multiple models...")
    
    # Dictionary of models to test
    models = {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42)
    }

    best_model_name = None
    best_model = None
    best_mae = float('inf') # Set starting best MAE to infinity

    print("\n=== Model Results ===")
    
    # 5. Evaluate and select the best model
    for name, model in models.items():
        # Train the model
        model.fit(X_train, y_train)
        
        # Test the model
        predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        
        print(f"{name} MAE: {mae:.2f} bikes")

        # Check if this is the best model so far
        if mae < best_mae:
            best_mae = mae
            best_model_name = name
            best_model = model

    print(f"\n🏆 Best Model: {best_model_name} with an MAE of {best_mae:.2f}")

    # 6. Export the Best Model for Phase 5 (The Web App)
    print(f"\nSaving the winning model ({best_model_name}) to disk as 'bike_model.pkl'...")
    joblib.dump(best_model, '/opt/airflow/project/bike_model.pkl')
    print("Done! The model is ready for live predictions.")

if __name__ == "__main__":
    main()