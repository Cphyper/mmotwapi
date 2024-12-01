
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import requests

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Custom ChatGPT API",
    description="A FastAPI application that mimics ChatGPT functionality.",
    version="1.0.0",
)

# CORS Configuration
origins = [
    "https://chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",  # Replace with your GoDaddy-hosted app domain
    "http://chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
    "https://www.chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
    "http://www.chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
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

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7

class Choice(BaseModel):
    message: Message

class ChatResponse(BaseModel):
    choices: List[Choice]

# Function to Generate Response
def generate_response(user_input: str, session_id: Optional[str] = None) -> str:
    """
    Calls the GPT model API hosted at your specified endpoint.
    """
    gpt_api_url = "https://mmotwapi.onrender.com/chat"  # Replace with your GPT API URL
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"input": user_input, "session_id": session_id}

    try:
        response = requests.post(gpt_api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        return data.get("output", "No response received from GPT.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error calling GPT API: {str(e)}")

# API Endpoint

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(chat_request: ChatRequest, x_api_key: str = Header(..., alias="x-api-key")):
    """
    Chat endpoint that processes user input and returns a response.
    Requires a valid API key in the 'x-api-key' header.
    """
    # Validate API Key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    try:
        # Extract user message from messages list
        user_message = ""
        for msg in chat_request.messages:
            if msg.role.lower() == "user":
                user_message = msg.content
                break

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found in the request.")

        # Generate response using the provided user input
        response_text = generate_response(user_message)

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
