from bson import ObjectId  # bson = binary JSON, the data format used by MongoDB
from bson import ObjectId
from fastapi import APIRouter, HTTPException, File, UploadFile
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import os
from models import SafetyResponse
from services.llm_service import process_documents_with_assistant
from services.audio_service import AudioTranscriber
from openai import OpenAI
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize OpenAI client
client = OpenAI()  # Make sure OPENAI_API_KEY is set in your environment variables
pdf_paths = [
    "prompts/nr-12-atualizada-2022-1.pdf",
    "prompts/WEG-w22-three-phase-electric-motor-50029265-brochure-english-web.pdf",
    "prompts/WEG-WMO-iom-installation-operation-and-maintenance-manual-of-electric-motors-50033244-manual-pt-en-es-web.pdf"
]
csv_path = "prompts/equipamentos.csv"


class MyJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # this will return the ID as a string
        return json.JSONEncoder.default(self, o)


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
        resposta = await process_documents_with_assistant(pdf_paths, csv_path, problema, client)
        response_dict = resposta.model_dump()

        db = db_connection.get_db()
        if db is not None:
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
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}")


@router.get("/getServices")
async def get_services():
    """Retrieve all service orders."""
    try:
        from app import db_connection
        db = db_connection.get_db()

        if db is not None:
            # If MongoDB is available, get from database
            mycol = db["serviceOrders"]
            print(list(mycol.find()))
            return json.loads(MyJSONEncoder().encode(list(mycol.find({}))))
        else:
            # If MongoDB is unavailable, get from file
            return load_from_file()

    except Exception as e:
        logger.error(f"Error in get_services: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving services: {str(e)}")


@router.post("/transcribe")
async def transcribe_audio():
    """Endpoint to handle audio transcription."""
    try:
        from app import db_connection
        db = db_connection.get_db()

        transcriber = AudioTranscriber()
        transcription = transcriber.transcribe_from_microphone()
        resposta = await process_documents_with_assistant(pdf_paths, csv_path, transcription, client)
        response_dict = resposta.model_dump()

        db = db_connection.get_db()
        if db is not None:
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
        logger.error(f"Error in transcribe_audio: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error transcribing audio: {str(e)}")


@router.get("/service/{item_id}")
async def read_item(item_id):
    from app import db_connection
    db = db_connection.get_db()
    if db is not None:
        # If MongoDB is available, get from database
        mycol = db["serviceOrders"]
        return json.loads(MyJSONEncoder().encode(mycol.find_one({'_id': ObjectId(item_id)})))


@router.post("/audioupload/")
async def create_upload_file(file: UploadFile):
    from app import db_connection
    try:
        transcriber = AudioTranscriber()
        audio_bytes = await file.read()
        transcription = transcriber.transcribe_audio_data(audio_bytes)
        resposta = await process_documents_with_assistant(pdf_paths, csv_path, transcription, client)
        response_dict = resposta.model_dump()

        db = db_connection.get_db()
        if db is not None:
            # If MongoDB is available, save to database
            mycol = db["serviceOrders"]
            res = mycol.insert_one(response_dict)
            logger.info("Service order saved to MongoDB")
            return {"transcription": transcription, "id": str(res.inserted_id)}
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
        logger.error(f"Error in transcribe_audio: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error transcribing audio: {str(e)}")
    return {"filename": file.filename}
