from riva.client import Auth, SpeechSynthesisService
import wave
import os

def get_riva_tts_service():
    RIVA_URI = "fastpitch-hifigan-tts:50052"
    auth = Auth(uri=RIVA_URI)
    tts_service = SpeechSynthesisService(auth)
    os.makedirs("audio_outputs", exist_ok=True)
    return tts_service

def generate_tts(text, filename="assistant_output.wav"):
    try:
        print("[INFO] Generate TTS Start")
        tts_service = get_riva_tts_service()
        response = tts_service.synthesize(
            text=text,
            voice_name="English-US.Female-1",
            language_code="en-US",
            sample_rate_hz=44100
        )
        
        audio_path = f"audio_outputs/{filename}"
        

        with wave.open(audio_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  
            wav_file.setsampwidth(2)  
            wav_file.setframerate(44100)
            

            wav_file.writeframes(response.audio)
        print("[INFO]  Generate TTS End: ",audio_path)
            
        return audio_path
        
    except Exception as e:
        print(f"TTS Generation Error: {str(e)}")
        return None