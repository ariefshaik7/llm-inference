from fastapi import FastAPI, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from transformers import pipeline
from prometheus_fastapi_instrumentator import Instrumentator, Info
import database
from contextlib import asynccontextmanager

# Lifespan manager to handle startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    database.Initialize_db()
    
    # Load the model on startup
    global model
    try:
        model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None
    
    yield
    
    # Clean up resources on shutdown if needed
    model = None
    print("Application shutdown: Model unloaded.")

app = FastAPI(title="LLM Inference API", lifespan=lifespan)

# --- Prometheus Instrumentation ---

# Custom function to add api_key label to metrics
def get_api_key_label(info: Info) -> None:
    api_key = info.request.headers.get("x-api-key", "none")
    info.labels["api_key"] = api_key

# Set up the instrumentator
instrumentator = Instrumentator(
    excluded_handlers=["/metrics"],
)
instrumentator.add(get_api_key_label) # Correctly add the custom instrumentation
instrumentator.instrument(app).expose(app)

# --- Model placeholder ---
model = None

class TextInput(BaseModel):
    text: str

async def verify_api_key(x_api_key: str = Header(...)):
    """
    This dependency checks the X-API-Key header.
    1. It gets the key from the request header.
    2. It checks if the user exists in the database.
    3. It verifies the user is active and has credits.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is missing")
    
    user = database.get_user(x_api_key)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")
        
    if user["credits"] <= 0:
        raise HTTPException(status_code=429, detail="Insufficient credits. Please top up.")
        
    return x_api_key

@app.get("/")
def read_root():
    return {"Message": "Sentiment Analysis API is live!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict")
def predict(data: TextInput, api_key: str = Depends(verify_api_key)):
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not available.")
    
    database.consume_credit(api_key)
    prediction = model(data.text)
    result = prediction
    user = database.get_user(api_key)

    return {
        "sentiment_prediction": result,
        "remaining_credits": user["credits"]
    }