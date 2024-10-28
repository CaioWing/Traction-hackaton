from bson import ObjectId  # bson = binary JSON, the data format used by MongoDB
from bson import ObjectId
from fastapi import APIRouter, HTTPException, File, UploadFile
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import os
from models import SafetyResponse
from services.llm_service import process_documents_with_assistant
from services.offline_service import generate_service_order_pdf
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


def load_service_order(item_id: str):
    """Load service order from MongoDB or file system."""
    try:
        from app import db_connection
        db = db_connection.get_db()
        
        if db is not None:
            # If MongoDB is available, get from database
            mycol = db["serviceOrders"]
            service_order = mycol.find_one({'_id': ObjectId(item_id)})
            if service_order:
                # Convert ObjectId to string
                service_order['_id'] = str(service_order['_id'])
                return service_order
        else:
            # If MongoDB is unavailable, get from file
            services = load_from_file()
            for service in services:
                if service.get('_id') == item_id:
                    return service
        
        return None
    except Exception as e:
        logger.error(f"Error loading service order: {str(e)}")
        return None

def load_from_file(filename: str = "service_orders.json") -> list:
    """Load data from JSON file when MongoDB is unavailable"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading from file: {str(e)}")
        return []

@router.get("/service/{item_id}/pdf")
async def generate_pdf(item_id: str, download: Optional[bool] = False):
    """
    Generate a PDF for a specific service order.
    
    Args:
        item_id: The ID of the service order
        download: If True, the PDF will be downloaded instead of viewed in browser
    
    Returns:
        FileResponse: The generated PDF file
    """
    try:
        # Get the service order
        service_order = load_service_order(item_id)
        if not service_order:
            raise HTTPException(
                status_code=404,
                detail="Service order not found"
            )
        
        # Create output directory if it doesn't exist
        output_dir = "output/pdf"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the PDF
        pdf_path = generate_service_order_pdf(service_order, output_dir)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate PDF"
            )
        
        # Set the filename for download
        filename = os.path.basename(pdf_path)
        
        # Return the PDF file
        headers = {
            'Content-Disposition': f'{"attachment" if download else "inline"}; filename="{filename}"'
        }
        
        return FileResponse(
            path=pdf_path,
            headers=headers,
            media_type='application/pdf'
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )

@router.get("/service/bulk-pdf")
async def generate_bulk_pdf(service_ids: str):
    """
    Generate PDFs for multiple service orders and return them as a zip file.
    
    Args:
        service_ids: Comma-separated list of service order IDs
    
    Returns:
        FileResponse: A zip file containing all generated PDFs
    """
    try:
        from zipfile import ZipFile
        import tempfile
        
        # Parse service IDs
        id_list = [id.strip() for id in service_ids.split(',')]
        
        # Create temporary directory for PDFs
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_files = []
            
            # Generate PDFs for each service order
            for service_id in id_list:
                service_order = load_service_order(service_id)
                if service_order:
                    pdf_path = generate_service_order_pdf(service_order, temp_dir)
                    if os.path.exists(pdf_path):
                        pdf_files.append(pdf_path)
            
            if not pdf_files:
                raise HTTPException(
                    status_code=404,
                    detail="No valid service orders found"
                )
            
            # Create zip file
            zip_path = os.path.join(temp_dir, "service_orders.zip")
            with ZipFile(zip_path, 'w') as zip_file:
                for pdf_file in pdf_files:
                    zip_file.write(pdf_file, os.path.basename(pdf_file))
            
            # Return the zip file
            return FileResponse(
                path=zip_path,
                headers={'Content-Disposition': 'attachment; filename="service_orders.zip"'},
                media_type='application/zip'
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating bulk PDFs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating bulk PDFs: {str(e)}"
        )


@router.get("/addService")
async def add_service(problema: str = "Preciso de uma manutenção na minha máquina de prensa"):
    """Add a new service order based on the safety analysis."""
    try:
        from app import db_connection
        resposta = await process_documents_with_assistant(pdf_paths, csv_path, problema, client)
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
    try:
        transcriber = AudioTranscriber()
        audio_bytes = await file.read()
        transcription = transcriber.transcribe_audio_data(audio_bytes)
        
        return {"transcription": transcription}
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error transcribing audio: {str(e)}")
    return {"filename": file.filename}
