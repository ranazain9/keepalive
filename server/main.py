"""
KeepAlive FastAPI Server
Streams microphone audio to AssemblyAI Real-Time WebSocket, passes transcript
to Agent #1 (TriageAgent) in <1ms, and returns live protocol decisions.
"""

import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
import websockets

from server.core.config import config
from server.core.logger import logger
from server.agents.triage.agent import TriageAgent
from server.agents.safety_coach.agent import SafetyCoachAgent
from server.agents.companion.agent import CompanionAgent
from server.tools.dispatcher_tool import trigger_emergency_dispatch, find_nearest_aed
from server.schemas.emergency import TriageAction, EmergencyIntent, PatientType

from server.services.orchestrator_service import RescueOrchestrator
from server.api.routes import (
    make_session_router,
    make_triage_router,
    make_safety_coach_router,
    make_companion_router,
    make_dispatch_router
)

app = FastAPI(title=config.APP_NAME, version=config.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Instantiate Core Orchestrator Service
orchestrator = RescueOrchestrator()

# 2. Backward-compatibility Facade exports (preserves unit test imports)
triage_agent = orchestrator.triage_agent
safety_coach = orchestrator.safety_coach
companion_agent = orchestrator.companion_agent
process_rescue_utterance = orchestrator.process_utterance

# 3. Mount Modular API Routers
app.include_router(make_session_router(orchestrator))
app.include_router(make_triage_router(orchestrator))
app.include_router(make_safety_coach_router(orchestrator))
app.include_router(make_companion_router(orchestrator))
app.include_router(make_dispatch_router())

import urllib.parse

# AssemblyAI v3 Streaming WebSocket endpoint (Universal-3.5 Pro) with Medical Emergency Word Boosting
MEDICAL_BOOST_TERMS = json.dumps([
    "sternum", "tourniquet", "femoral", "brachial", "agonal", 
    "naloxone", "epipen", "compressions", "defibrillator", "narcan",
    "unresponsive", "carotid", "c-spine", "anaphylaxis", "hemorrhage",
    "paramedics", "paramedic", "ambulance", "ems"
])
AAI_WS_URL = f"wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&word_boost={urllib.parse.quote(MEDICAL_BOOST_TERMS)}"

@app.get("/")
async def get_test_page():
    """Serves the real-time voice testing dashboard."""
    with open("client_test.html", "r", encoding="utf-8") as f:
        return HTMLResponse(
            content=f.read(),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

@app.websocket("/ws/triage")
async def websocket_triage_endpoint(client_ws: WebSocket):
    await client_ws.accept()
    logger.info("🎙️ Client microphone connected to /ws/triage")
    
    # Extract client location metadata from query string if available
    client_location = client_ws.query_params.get("location")
    client_lat = float(client_ws.query_params.get("lat", 37.7749))
    client_lon = float(client_ws.query_params.get("lon", -122.4194))
    
    api_key = config.ASSEMBLYAI_API_KEY
    if not api_key or api_key == "your_assemblyai_api_key_here":
        await client_ws.send_json({
            "error": "AssemblyAI API Key is missing or invalid in .env file."
        })
        await client_ws.close()
        return

    # Connect to AssemblyAI v3 Streaming WebSocket
    headers = {"Authorization": api_key}
    
    try:
        try:
            connect_cm = websockets.connect(AAI_WS_URL, additional_headers=headers, open_timeout=10, ping_interval=5, ping_timeout=10)
        except TypeError:
            connect_cm = websockets.connect(AAI_WS_URL, extra_headers=headers, open_timeout=10, ping_interval=5, ping_timeout=10)

        async with connect_cm as aai_ws:
            logger.info("⚡ Connected to AssemblyAI v3 Streaming WebSocket")
            
            # 1. Forward raw PCM audio bytes directly to v3 WebSocket
            async def forward_audio():
                try:
                    while True:
                        data = await client_ws.receive_bytes()
                        await aai_ws.send(data)
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.warning(f"Audio forward closed: {e}")

            # 2. Receive transcript from AssemblyAI v3 -> Run Agent 1, 2, 3 -> Client
            async def receive_transcripts():
                try:
                    async for message in aai_ws:
                        msg_data = json.loads(message)
                        msg_type = msg_data.get("type")
                        
                        if msg_type not in ["Begin", "Heartbeat"]:
                            logger.info(f"⚡ [AAI v3 Event] type={msg_type} keys={list(msg_data.keys())}")
                        
                        transcript_text = ""
                        is_final = False
                        if msg_type in ["Turn", "TurnEvent"]:
                            transcript_text = msg_data.get("transcript", "").strip()
                            is_final = bool(msg_data.get("end_of_turn", False))
                        elif "transcript" in msg_data:
                            transcript_text = msg_data.get("transcript", "").strip()
                            is_final = bool(msg_data.get("end_of_turn", True))
                        elif "text" in msg_data:
                            transcript_text = msg_data.get("text", "").strip()
                            is_final = True
                        
                        if transcript_text:
                            # 1. Live interim transcription: update caller screen immediately without multi-agent churn
                            if not is_final:
                                await client_ws.send_json({
                                    "type": "PARTIAL_TRANSCRIPT",
                                    "transcript": transcript_text
                                })
                                continue

                            # 2. Final speech turn: Rescuer completed utterance -> Execute coordinated multi-agent pipeline
                            logger.info(f"🗣️ Transcribed [Turn Final]: \"{transcript_text}\"")
                            
                            res = process_rescue_utterance(
                                transcript_text,
                                location=client_location,
                                lat=client_lat,
                                lon=client_lon
                            )

                            await client_ws.send_json({
                                "type": "TRIAGE_UPDATE",
                                "is_final": True,
                                "transcript": transcript_text,
                                "triage": res["triage"].model_dump(),
                                "directive": res["directive"].model_dump() if res["directive"] else None,
                                "companion_answer": res["companion_answer"],
                                "cad_dispatch": res["cad_dispatch"],
                                "aed_info": res["aed_info"],
                                "handoff_card": res["handoff_card"].model_dump() if res["handoff_card"] else None,
                                "agent_1_status": res["agent_1_status"],
                                "agent_2_status": res["agent_2_status"],
                                "agent_3_status": res["agent_3_status"],
                                "companion_model": res["companion_model"]
                            })
                except Exception as e:
                    logger.warning(f"Transcript receiver closed: {e}")

            await asyncio.gather(forward_audio(), receive_transcripts())

    except Exception as e:
        logger.error(f"AssemblyAI connection error: {e}")
        await client_ws.send_json({"error": str(e)})
    finally:
        logger.info("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
