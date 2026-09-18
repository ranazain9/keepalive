"""
KeepAlive Core Configuration
Defines system-wide thresholds, clinical constants, and latency requirements.
Loads environment variables from .env file.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class TriageConfig(BaseModel):
    # Minimum confidence to instantly lock protocol (>= 0.82)
    CONFIDENCE_LOCK_THRESHOLD: float = float(os.getenv("CONFIDENCE_LOCK_THRESHOLD", 0.82))
    
    # Ambiguous confidence zone (0.60 <= score < 0.82) triggering 1-second probe
    CONFIDENCE_AMBIGUOUS_THRESHOLD: float = float(os.getenv("CONFIDENCE_AMBIGUOUS_THRESHOLD", 0.60))
    
    # Maximum allowed latency budget for Agent 1 classification (in milliseconds)
    MAX_LATENCY_BUDGET_MS: float = 10.0
    
    # Target Metronome BPM for Sudden Cardiac Arrest CPR
    CPR_TARGET_BPM: int = 110

class AppConfig(BaseModel):
    APP_NAME: str = "KeepAlive Emergency Voice Cockpit"
    VERSION: str = "1.0.0-champion"
    ASSEMBLYAI_API_KEY: str = os.getenv("ASSEMBLYAI_API_KEY", "").strip('"').strip("'").strip()
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip('"').strip("'").strip()
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Real CAD & Dispatch Relay Configuration
    CAD_PROVIDER: str = os.getenv("CAD_PROVIDER", "MOCK")  # MOCK, RAPIDSOS, WEBHOOK, TWILIO, NTFY
    CAD_WEBHOOK_URL: str = os.getenv("CAD_WEBHOOK_URL", "")
    RAPIDSOS_API_KEY: str = os.getenv("RAPIDSOS_API_KEY", "")
    NTFY_TOPIC: str = os.getenv("NTFY_TOPIC", "MWjc3TasJqBWGh10")
    
    # Twilio Telephony Configuration (Optional real calls/SMS)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
    EMERGENCY_CONTACT_NUMBER: str = os.getenv("EMERGENCY_CONTACT_NUMBER", "")
    
    triage: TriageConfig = TriageConfig()

config = AppConfig()
