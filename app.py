from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd

# 1. Initialize the API
app = FastAPI(
    title="Bike Share ML API",
    description="Predicts the number of available bikes at a station.",
    version="1.0"
)

# 2. Load the Brain (The Random Forest Model)
try:
    model = joblib.load('bike_model.pkl')
    print("Random Forest model successfully loaded into memory!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# 3. Define the Expected Input (The Data Contract)
class PredictionRequest(BaseModel):
    hour_of_day: int
    day_of_week: int
    is_weekend: bool
    temperature_celsius: float

# 4. Create the Prediction Endpoint
@app.post("/predict")
def predict_bikes(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded on the server.")

    # Convert the incoming JSON request into a Pandas DataFrame
    # The columns MUST perfectly match what the model was trained on
    input_data = pd.DataFrame([{
        'hour_of_day': request.hour_of_day,
        'day_of_week': request.day_of_week,
        'is_weekend': request.is_weekend,
        'temperature_celsius': request.temperature_celsius
    }])

    # Ask the Random Forest to predict
    prediction = model.predict(input_data)
    
    # Return the result as JSON
    return {
        "estimated_bikes_available": round(prediction[0], 1),
        "inputs_received": request.dict()
    }