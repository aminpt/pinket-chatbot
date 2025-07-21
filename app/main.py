from fastapi import FastAPI
from app.services.api_service import APIService

app = FastAPI()

# Initialize the API Service
api_service = APIService()