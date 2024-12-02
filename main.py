from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from typing import List
import os
import base64
import logging
from playwright.sync_api import sync_playwright

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Dress to Impress API",
    description="Analyze outfits based on event, zip code, and time, then grade them.",
    version="1.0.0",
)

# Pydantic model for the final JSON response
class Message(BaseModel):
    role: str
    content: str

class Choice(BaseModel):
    message: Message

class ChatResponse(BaseModel):
    choices: List[Choice]

# Environment variables
API_KEY = os.getenv("API_KEY", "16546sw60520e19st")  # Replace with your actual API key

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
        # Read and encode the uploaded image
        image_content = await image.read()
        logger.info(f"Received image: {image.filename}, event: {event}, zip: {zip_code}, month: {month}")
        image_base64 = base64.b64encode(image_content).decode("utf-8")

        # Generate prompt
        prompt = (
            f"Event: {event}\n"
            f"Zip Code: {zip_code}\n"
            f"Month: {month}\n"
            f"Image (Base64): {image_base64[:50]}... (truncated)\n\n"
            "Please analyze the outfit for the event, grade it from A to F, and provide improvement suggestions."
        )

        # Use Playwright to interact with the GPT instance
        logger.info("Interacting with the custom GPT instance...")
        response_text = interact_with_gpt_instance(prompt)
        logger.info(f"Received response from GPT: {response_text}")

        # Format the response as JSON
        return ChatResponse(
            choices=[
                Choice(message=Message(role="assistant", content=response_text))
            ]
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail="Server error occurred.")

def interact_with_gpt_instance(prompt: str) -> str:
    """
    Use Playwright to send a prompt to the GPT instance and retrieve the response.
    """
    gpt_url = "https://chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Go to the GPT instance
            page.goto(gpt_url)

            # Interact with the page (adjust selectors based on the page's structure)
            logger.info("Entering the prompt into the GPT interface...")
            page.fill("textarea", prompt)  # Replace "textarea" with the correct selector for the input field
            page.click("button[type='submit']")  # Replace with the correct selector for the submit button

            # Wait for the response
            page.wait_for_selector(".response-container")  # Adjust based on the page's response element
            response_text = page.query_selector(".response-container").inner_text()  # Adjust based on the response container

            browser.close()
            return response_text
    except Exception as e:
        logger.error(f"Error interacting with GPT instance: {e}")
        raise HTTPException(status_code=500, detail="Failed to interact with GPT instance.")
