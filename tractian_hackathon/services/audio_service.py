import os
import io
import logging
from typing import Optional
import speech_recognition as sr
from openai import OpenAI
from openai.types.audio import Transcription

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioRecognitionError(Exception):
    """Custom exception for audio recognition related errors."""
    pass

class AudioTranscriber:
    """Handles audio recording and transcription using OpenAI's Whisper model."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        ambient_duration: int = 5
    ):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        self.model = model
        self.ambient_duration = ambient_duration
        self.client = OpenAI(api_key=self.api_key)
        self.recognizer = sr.Recognizer()
    
    def record_speech(self) -> bytes:
        """Record speech from microphone and return the audio data."""
        try:
            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self.ambient_duration
                )
                
                logger.info("Listening for speech...")
                audio = self.recognizer.listen(source)
                
                return audio.get_wav_data()
                
        except sr.UnknownValueError:
            raise AudioRecognitionError("Could not understand the audio")
        except Exception as e:
            raise AudioRecognitionError(f"Error recording audio: {str(e)}")
    
    def transcribe_audio_data(self, audio_data: bytes) -> str:
        """Transcribe audio data using OpenAI's Whisper model."""
        try:
            audio_io = io.BytesIO(audio_data)
            audio_io.name = 'audio.wav'
            
            transcription: Transcription = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_io
            )
            logger.info("Audio transcription completed")
            return transcription.text
                
        except Exception as e:
            raise AudioRecognitionError(f"Error transcribing audio: {str(e)}")
    
    def transcribe_from_microphone(self) -> str:
        """Record speech and transcribe it in one step."""
        try:
            audio_data = self.record_speech()
            return self.transcribe_audio_data(audio_data)
            
        except Exception as e:
            raise AudioRecognitionError(f"Error in transcription pipeline: {str(e)}")