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

# Load environment variables from .env file if exists (optional for local testing)
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

# Initialize Google Vision Client with credentials from environment variables
def get_vision_client():
    service_account_info = os.getenv("GOOGLE_CLOUD_KEY_JSON")
    if not service_account_info:
        raise Exception("Google Cloud service account key not found in environment variables.")
    try:
        decoded_key = base64.b64decode(service_account_info)
        service_account_dict = json.loads(decoded_key)
        credentials = service_account.Credentials.from_service_account_info(service_account_dict)
        return vision.ImageAnnotatorClient(credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to initialize Google Vision Client: {e}")
        raise

vision_client = get_vision_client()

# Pydantic Models
class Message(BaseModel):
    role: str
    content: str

class Choice(BaseModel):
    message: Message

class ChatResponse(BaseModel):
    choices: List[Choice]

# Function to Analyze Image
def analyze_image(image: UploadFile) -> str:
    """
    Analyzes the uploaded image using Google Vision API and returns a description.
    """
    try:
        contents = image.file.read()
        image_content = vision.Image(content=contents)
        response = vision_client.label_detection(image=image_content)
        labels = response.label_annotations
        if response.error.message:
            raise Exception(response.error.message)
        
        # Create a description from labels
        description = ", ".join([label.description for label in labels])
        logger.info(f"Image analysis description: {description}")
        return description
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise Exception(f"Image analysis failed: {str(e)}")
    finally:
        image.file.close()

# Function to Generate Response
def generate_response(description: str, event: str, zip_code: str, month: str) -> str:
    """
    Calls the GPT model API with the image description and event details.
    """
    gpt_api_url = "https://mmotwapi.onrender.com/chat"  # Replace with your FastAPI Render URL
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    
    prompt = (
        f"Event: {event}\n"
        f"Zip Code: {zip_code}\n"
        f"Month: {month}\n"
        f"Image Description: {description}\n\n"
        "Please analyze the image and provide a grade from A to F based on suitability for the event. "
        "Include reasons for the grade and recommendations to improve to an A."
    )
    
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": prompt}
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
        logger.error(f"Error calling GPT API: {e}")
        raise Exception(f"Error calling GPT API: {str(e)}")

# API Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    x_api_key: str = Header(..., alias="x-api-key"),
    image: UploadFile = File(...),
    event: str = Form(...),
    zip_code: str = Form(...),
    month: str = Form(...)
):
    """
    Chat endpoint that processes user input including an image and event details,
    then returns a response with a grade and recommendations.
    Requires a valid API key in the 'x-api-key' header.
    """
    # Validate API Key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    try:
        # Log the incoming request details (excluding the image for privacy)
        logger.info(f"Received request: event={event}, zip_code={zip_code}, month={month}")

        # Analyze the uploaded image
        description = analyze_image(image)

        # Generate response using the image description and event details
        response_text = generate_response(description, event, zip_code, month)

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

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
