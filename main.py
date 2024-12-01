from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import base64
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
from google.cloud import vision
from google.oauth2 import service_account


# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Custom ChatGPT API",
    description="A FastAPI application that mimics ChatGPT functionality.",
    version="1.0.0",
)

# CORS Configuration
origins = [
    "https://chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
    "http://chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
    "https://www.chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
    "http://www.chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specified origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch API_KEY from environment variables
API_KEY = os.getenv("API_KEY", "16546sw60520e19st")  # Replace with your actual API key

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
    gpt_api_url = "https://mmotwapi.onrender.com/chat"  # Replace with your FastAPI Render URL
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(gpt_api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        logger.info(f"Response from GPT API: {data}")
        return data.get("choices", [{}])[0].get("message", {}).get("content", "No response.")
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
        # Log the incoming request
        logger.info(f"Received request: {chat_request.dict()}")

        # Extract user message from messages list
        user_message = next(
            (msg.content for msg in chat_request.messages if msg.role.lower() == "user"),
            None
        )
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found in the request.")

        # Generate response using the provided user input
        response_text = generate_response(user_message)

        # Construct the response
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

        logger.info(f"Generated response: {response}")
        return response

    except Exception as e:
        logger.error(f"Error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
