from fastapi import APIRouter, HTTPException
from typing import List, Optional
import os
from models import SafetyResponse
from services.llm_service import process_pdf_with_assistant
from services.audio_service import AudioTranscriber
from openai import OpenAI
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize OpenAI client
client = OpenAI()  # Make sure OPENAI_API_KEY is set in your environment variables
pdf_path = "prompts/nr-12-atualizada-2022-1.pdf"

def save_to_file(data: dict, filename: str = "service_orders.json"):
    """Save data to a JSON file when MongoDB is unavailable"""
    try:
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        existing_data.append(data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving to file: {str(e)}")
        return False

def load_from_file(filename: str = "service_orders.json") -> List[dict]:
    """Load data from JSON file when MongoDB is unavailable"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading from file: {str(e)}")
        return []

@router.get("/addService")
async def add_service(problema: str = "Preciso de uma manutenção na minha máquina de prensa"):
    """Add a new service order based on the safety analysis."""
    try:
        from app import db_connection
        resposta = await process_pdf_with_assistant(pdf_path, problema, client)
        response_dict = resposta.model_dump()
        
        db = db_connection.get_db()
        if db:
            # If MongoDB is available, save to database
            mycol = db["serviceOrders"]
            mycol.insert_one(response_dict)
            logger.info("Service order saved to MongoDB")
        else:
            # If MongoDB is unavailable, save to file
            save_success = save_to_file(response_dict)
            if not save_success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to save service order to backup file"
                )
            logger.info("Service order saved to file")
            
        return {"message": "Added with success!", "data": response_dict}
    
    except Exception as e:
        logger.error(f"Error in add_service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/getServices")
async def get_services() -> List[SafetyResponse]:
    """Retrieve all service orders."""
    try:
        from app import db_connection
        db = db_connection.get_db()
        
        if db:
            # If MongoDB is available, get from database
            mycol = db["serviceOrders"]
            return list(mycol.find({}, {'_id': False}))
        else:
            # If MongoDB is unavailable, get from file
            return load_from_file()
            
    except Exception as e:
        logger.error(f"Error in get_services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving services: {str(e)}")

@router.post("/transcribe")
async def transcribe_audio():
    """Endpoint to handle audio transcription."""
    try:
        transcriber = AudioTranscriber()
        transcription = transcriber.transcribe_from_microphone()
        return {"transcription": transcription}
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")