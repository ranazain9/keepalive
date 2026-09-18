import os
from dotenv import load_dotenv
import assemblyai as aai

load_dotenv()
api_key = os.getenv("ASSEMBLYAI_API_KEY", "").strip('"').strip("'").strip()
aai.settings.api_key = api_key

def on_open(session_opened: aai.RealtimeSessionOpened):
    print("SUCCESS: AssemblyAI Real-Time Session Opened with ID:", session_opened.session_id)

def on_data(transcript: aai.RealtimeTranscript):
    if transcript.text:
        print(f"Transcript: {transcript.text}")

def on_error(error: aai.RealtimeError):
    print("AssemblyAI Error:", error)

def on_close():
    print("Session closed")

transcriber = aai.RealtimeTranscriber(
    sample_rate=16_000,
    on_data=on_data,
    on_error=on_error,
    on_open=on_open,
    on_close=on_close
)

print("Connecting to AssemblyAI RealtimeTranscriber...")
transcriber.connect()
print("Connected successfully! Now closing...")
transcriber.close()
