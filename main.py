from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from typing import List
import os
import logging
import base64
from playwright.async_api import async_playwright

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
API_KEY = os.getenv("API_KEY", "16546sw60520e19st")  # Replace with your actual API key

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
        logger.error("Invalid API Key")
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    try:
        # Log step: Reading uploaded image
        logger.info("Reading uploaded image...")
        image_content = await image.read()
        if not image_content:
            logger.error("Uploaded image is empty")
            raise HTTPException(status_code=400, detail="Uploaded image is empty")

        logger.info(f"Received image: {image.filename} (size: {len(image_content)} bytes)")

        # Convert image to Base64
        logger.info("Encoding image to Base64...")
        image_base64 = base64.b64encode(image_content).decode("utf-8")
        logger.info(f"Image encoded successfully. Truncated data: {image_base64[:50]}")

        # Prepare GPT prompt
        logger.info("Preparing GPT prompt...")
        prompt = (
            f"Event: {event}\n"
            f"Zip Code: {zip_code}\n"
            f"Month: {month}\n"
            f"Image (Base64): {image_base64[:50]}... (truncated)\n\n"
            "Please analyze the outfit for the event, grade it from A to F, and provide improvement suggestions."
        )

        # Call the GPT instance via Playwright
        logger.info("Interacting with GPT instance via Playwright...")
        response_text = await interact_with_gpt_instance(prompt)
        logger.info(f"Received response from GPT: {response_text}")

        # Return the response
        return ChatResponse(
            choices=[
                Choice(message=Message(role="assistant", content=response_text))
            ]
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail="Server error occurred.")

async def interact_with_gpt_instance(prompt: str) -> str:
    """
    Use Playwright to send a prompt to the GPT instance and retrieve the response asynchronously.
    """
    gpt_url = "https://chatgpt.com/g/g-674ca726c78c8191a3ca4baede9712a6-dress-to-impress"
    playwright_path = "/opt/render/.cache/ms-playwright/chromium_headless_shell-1148/chrome-linux/headless_shell"

    try:
        async with async_playwright() as p:
            # Launch the browser with the specified executable path
            browser = await p.chromium.launch(
                executable_path=playwright_path,  # Explicit path to headless_shell
                headless=True
            )
            page = await browser.new_page()

            # Navigate to the GPT instance
            await page.goto(gpt_url)

            # Interact with the page (adjust selectors based on the page's structure)
            await page.fill("textarea", prompt)  # Replace with the correct selector for the input field
            await page.click("button[type='submit']")  # Replace with the correct selector for the submit button

            # Wait for the response
            await page.wait_for_selector(".response-container")  # Adjust based on the page's response element
            response_text = await page.query_selector(".response-container").inner_text()  # Adjust based on the response container

            await browser.close()
            return response_text
    except Exception as e:
        logger.error(f"Error interacting with GPT instance: {e}")
        raise HTTPException(status_code=500, detail="Failed to interact with GPT instance.")
