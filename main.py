# main.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Fetch API_KEY from environment variables
API_KEY = os.getenv("API_KEY", "your-secure-api-key")

class ChatRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    metadata: Optional[dict] = None

def generate_response(user_input, session_id=None):
    # Replace this with your actual model inference logic
    response = f"Echo: {user_input}"
    return response

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(chat_request: ChatRequest, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    try:
        response_text = generate_response(chat_request.user_input, chat_request.session_id)
        metadata = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": chat_request.session_id or "N/A"
        }
        return ChatResponse(response=response_text, metadata=metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

