# main.py

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Custom ChatGPT API",
    description="A FastAPI application that mimics ChatGPT functionality.",
    version="1.0.0",
)
# CORS Configuration
origins = [
    "https://chat.openai.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",  # Replace with your GoDaddy-hosted app domain
    "http://chat.openai.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
    "https://www.chat.openai.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
    "http://www.chat.openai.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
    # Add more origins if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # Allow specified origins
    allow_credentials=True,            # Allow cookies, authorization headers, etc.
    allow_methods=["*"],               # Allow all HTTP methods
    allow_headers=["*"],               # Allow all headers
)

# Fetch API_KEY from environment variables
API_KEY = os.getenv("API_KEY", "your-default-api-key")  # Replace with a strong default or leave as is

# Pydantic Models

class Message(BaseModel):
    role: str
    content: str

class Choice(BaseModel):
    message: Message

class ChatResponse(BaseModel):
    choices: List[Choice]

# Sample Function to Generate Response
def generate_response(user_input: str, session_id: Optional[str] = None) -> str:
    """
    Replace this function with your actual ChatGPT model inference logic.
    For demonstration, it simply echoes the user input.
    """
    # TODO: Integrate your ChatGPT model or any other AI model here
    response = f"Echo: {user_input}"
    return response

# API Endpoint

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(chat_request: dict, x_api_key: str = Header(...)):
    """
    Chat endpoint that processes user input and returns a response.
    Requires a valid API key in the 'x-api-key' header.
    """
    # Validate API Key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    try:
        user_input = chat_request.get("messages", [{}])[1].get("content", "")
        response_text = generate_response(user_input)

        # Construct the response in OpenAI's format
        response = ChatResponse(
            choices=[
                Choice(
                    message=Message(
                        role="assistant",
                        content=response_text
                    )
                )
            ]
        )

        return response

    except Exception as e:
        # Handle any unexpected errors
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
