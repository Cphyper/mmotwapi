from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(
    title="Custom ChatGPT API",
    description="A FastAPI application that mimics ChatGPT functionality.",
    version="1.0.0",
)

# Existing POST Endpoint
@app.post("/chat")
def chat_endpoint():
    """
    This is your existing POST endpoint for processing chat requests.
    """
    return {"detail": "Processing POST requests only."}

# New GET Endpoint
@app.get("/chat")
def chat_info():
    """
    Provides helpful information for GET requests.
    """
    return {
        "message": "This is the Dress to Impress Grader API.",
        "instructions": "Use a POST request with appropriate JSON payload and API key.",
        "example_payload": {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Describe the outfit"}],
            "temperature": 0.7
        },
        "example_headers": {
            "Content-Type": "application/json",
            "x-api-key": "your-api-key"
        }
    }
