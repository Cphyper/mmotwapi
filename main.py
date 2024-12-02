from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from typing import List
import os
import requests
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Dress to Impress API",
    description="Analyze outfits based on event, zip code, and time, then grade them.",
    version="1.0.0",
)

# Pydantic model for GPT response
class Message(BaseModel):
    role: str
    content: str

class Choice(BaseModel):
    message: Message

class ChatResponse(BaseModel):
    choices: List[Choice]

# Environment variables
API_KEY = os.getenv("API_KEY", "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")  # GPT API Key
GPT_API_URL = "https://chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress"

# Endpoint to process uploaded image and form data
@app.post("/chat", response_model=ChatResponse)
async def analyze_outfit(
    image: UploadFile = File(...),
    event: str = Form(...),
    zip_code: str = Form(...),
    month: str = Form(...),
    x_api_key: str = Header(..., alias="x-api-key")
):
    """
    Endpoint to process outfit images and generate GPT responses.
    """
    # Validate API Key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    try:
        # Read the uploaded image
        image_content = await image.read()
        logger.info(f"Received image: {image.filename}, event: {event}, zip: {zip_code}, month: {month}")

        # Convert image to Base64
        import base64
        image_base64 = base64.b64encode(image_content).decode("utf-8")

        # Prepare the GPT prompt
        prompt = (
            f"Event: {event}\n"
            f"Zip Code: {zip_code}\n"
            f"Month: {month}\n"
            f"Image (Base64): {image_base64[:50]}... (truncated)\n\n"
            "Please analyze the outfit for the event, grade it from A to F, and provide improvement suggestions."
        )

        # Call GPT API
        headers = {"Content-Type": "application/json", "x-api-key": API_KEY}
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        response = requests.post(GPT_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        # Parse GPT API response
        gpt_response = response.json()
        logger.info(f"GPT API response: {gpt_response}")

        # Return the response
        return ChatResponse(
            choices=[
                Choice(message=Message(role="assistant", content=gpt_response.get("choices", [{}])[0].get("message", {}).get("content", "No response.")))
            ]
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail="Server error occurred.")
