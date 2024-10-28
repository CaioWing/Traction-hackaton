import os
import speech_recognition as sr
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

recognizer = sr.Recognizer()

def recognize_and_record_speech(output_file_path: str = "microphone_result.wav") -> None:
    try:
        # Use the microphone as the source for input
        with sr.Microphone() as source:
            print("Adjusting for ambient noise, please wait...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("Listening for speech...")

            # Capture the audio from the microphone
            audio = recognizer.listen(source)
        
        # write audio to a WAV file
        with open(output_file_path, "wb") as f:
            f.write(audio.get_wav_data())
        print(f'{output_file_path} recorded.')

    except sr.UnknownValueError:
        print("Sorry, I couldn't understand what you said.")
    

def transcript_speech(audio) -> str:
            
        transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio)            
        
        return transcription.text

def get_transcript_from_microphone_input() -> str:
     
    output_file = 'audio.wav'
    recognize_and_record_speech(output_file)
    
    with open(output_file) as audio:
        if audio:
            text = transcript_speech(audio)
            return text
        raise Exception('Audio not recorded.')


if __name__ == '__main__':

    with open('media\\requisicao_de_servico_audio.ogg', 'rb') as audio:

        text = transcript_speech(audio)
        print(text)