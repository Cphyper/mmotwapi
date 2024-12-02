from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import List, Optional
import requests
import os

app = FastAPI()

# Load API key from environment variable or configuration
API_KEY = os.getenv("API_KEY", "16546sw60520e19st")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7

@app.post("/chat")
async def chat_endpoint(chat_request: ChatRequest, x_api_key: str = Header(..., alias="x-api-key")):
    # Validate API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # Call the GPT-4 API or process the request (this is a mock example)
    gpt_api_url = "https://api.openai.com/v1/chat/completions"  # Replace with your GPT API endpoint
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = chat_request.dict()

    try:
        response = requests.post(gpt_api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling GPT API: {str(e)}")
