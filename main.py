# main.py

from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Optional, List
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for JSON data
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

# Middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise e
    logger.info(f"Response status: {response.status_code}")
    return response

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "message": "Validation Error",
            "errors": exc.errors(),
            "body": exc.body
        },
    )

# Custom exception handler for UnicodeDecodeError
@app.exception_handler(UnicodeDecodeError)
async def unicode_decode_exception_handler(request: Request, exc: UnicodeDecodeError):
    logger.error(f"Unicode decode error: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "message": "Unicode Decode Error",
            "detail": str(exc)
        },
    )

# Endpoint for handling JSON data
@app.post("/items/")
async def create_item(item: Item):
    logger.info(f"Creating item: {item}")
    return {"item": item}

# Endpoint for handling single file upload
@app.post("/upload/")
async def upload_file(file: bytes = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    logger.info(f"Received file of size: {len(file)} bytes")
    # Example processing: return file size
    return {"file_size": len(file)}

# Endpoint for handling multiple file uploads
@app.post("/uploadfiles/")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    results = []
    for file in files:
        contents = await file.read()
        logger.info(f"Received file: {file.filename}, size: {len(contents)} bytes")
        # Example processing: return file metadata
        results.append({
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(contents)
        })
    
    return {"uploaded_files": results}
