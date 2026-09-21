"""
KeepAlive FastAPI Server
Streams microphone audio to AssemblyAI Real-Time WebSocket, passes transcript
to Agent #1 (TriageAgent) in <1ms, and returns live protocol decisions.
"""

import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
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
AAI_WS_URL = f"wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&mode=min_latency&min_turn_silence=250&max_turn_silence=800&word_boost={urllib.parse.quote(MEDICAL_BOOST_TERMS)}"

from fastapi.staticfiles import StaticFiles

# Production static assets mounting for Next-Gen React Cockpit
if os.path.exists("client/dist"):
    if os.path.exists("client/dist/assets"):
        app.mount("/assets", StaticFiles(directory="client/dist/assets"), name="assets")
    if os.path.exists("client/dist/videos"):
        app.mount("/videos", StaticFiles(directory="client/dist/videos"), name="videos")
    app.mount("/cockpit", StaticFiles(directory="client/dist", html=True), name="cockpit")

@app.get("/")
async def get_root_page():
    """Serves the production React Rescue Cockpit if built, else client_test.html."""
    if os.path.exists("client/dist/index.html"):
        return FileResponse("client/dist/index.html")
    with open("client_test.html", "r", encoding="utf-8") as f:
        return HTMLResponse(
            content=f.read(),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

@app.get("/test")
async def get_test_page():
    """Serves the standalone browser testing suite."""
    with open("client_test.html", "r", encoding="utf-8") as f:
        return HTMLResponse(
            content=f.read(),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

@app.get("/health")
async def root_health_check():
    """Root health check for cloud platform load balancers (Render, AWS, GCP, K8s)."""
    return {
        "status": "HEALTHY",
        "app": config.APP_NAME,
        "version": config.VERSION,
        "agents": ["Agent1_Triage", "Agent2_SafetyCoach", "Agent3_Companion"]
    }

@app.get("/api/geocode")
async def reverse_geocode(lat: float = 37.7749, lon: float = -122.4194):
    """
    Secure server-side reverse geocoding with standard User-Agent.
    Eliminates browser-side HTTP 403 Forbidden errors from Nominatim.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "KeepAlive-Rescue-Agent/1.0 (emergency-cockpit@keepalive.app)"}
    )
    try:
        def _fetch():
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                return json.loads(resp.read().decode())
        data = await asyncio.to_thread(_fetch)
        display_name = data.get("display_name", "")
        parts = display_name.split(",")
        address = ", ".join(p.strip() for p in parts[:3]) if parts else display_name
        return {"address": address or f"{lat:.4f}, {lon:.4f}", "raw": data}
    except Exception as e:
        logger.warning(f"Geocode lookup fallback: {e}")
        return {"address": f"{lat:.4f}, {lon:.4f}", "error": str(e)}

# Concurrency guard: Ensures only 1 active streaming session to AssemblyAI
_active_aai_ws = None
_aai_ws_lock = asyncio.Lock()

@app.websocket("/ws/triage")
async def websocket_triage_endpoint(client_ws: WebSocket):
    global _active_aai_ws
    await client_ws.accept()
    logger.info("🎙️ Client microphone connected to /ws/triage")

    # Gracefully shut down any trailing connection to honor AssemblyAI 1-session concurrency policy
    async with _aai_ws_lock:
        if _active_aai_ws is not None:
            try:
                await _active_aai_ws.close()
                await asyncio.sleep(0.2)
            except Exception:
                pass
            _active_aai_ws = None
    
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

    # Connect to AssemblyAI v3 Streaming WebSocket with 25s timeout and automatic retry
    headers = {"Authorization": api_key}
    
    async def get_aai_connection():
        for attempt in range(2):
            try:
                try:
                    return await websockets.connect(
                        AAI_WS_URL,
                        additional_headers=headers,
                        open_timeout=25,
                        ping_interval=5,
                        ping_timeout=15
                    )
                except TypeError:
                    return await websockets.connect(
                        AAI_WS_URL,
                        extra_headers=headers,
                        open_timeout=25,
                        ping_interval=5,
                        ping_timeout=15
                    )
            except Exception as conn_err:
                if attempt == 0:
                    logger.warning(f"AssemblyAI handshake retry (attempt 1 failed: {conn_err})")
                    await asyncio.sleep(0.5)
                    continue
                raise conn_err

    try:
        aai_ws = await get_aai_connection()
        _active_aai_ws = aai_ws
        try:
            logger.info("⚡ Connected to AssemblyAI v3 Streaming WebSocket")
            
            # 1. Forward raw PCM audio bytes (or client text) directly
            async def forward_audio():
                try:
                    while True:
                        msg = await client_ws.receive()
                        if "bytes" in msg and msg["bytes"]:
                            await aai_ws.send(msg["bytes"])
                        elif "text" in msg and msg["text"]:
                            try:
                                payload = json.loads(msg["text"])
                                if payload.get("type") == "FALLBACK_SPEECH":
                                    txt = payload.get("text", "").strip()
                                    if txt:
                                        res = await asyncio.to_thread(
                                            process_rescue_utterance,
                                            txt,
                                            location=client_location,
                                            lat=client_lat,
                                            lon=client_lon
                                        )
                                        await client_ws.send_json({
                                            "type": "TRIAGE_UPDATE",
                                            "is_final": True,
                                            "transcript": txt,
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
                            except Exception as pe:
                                logger.warning(f"Client text parse error: {pe}")
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
                            # 1. Live interim transcription: update caller screen immediately
                            if not is_final:
                                await client_ws.send_json({
                                    "type": "PARTIAL_TRANSCRIPT",
                                    "transcript": transcript_text
                                })
                                
                                # Fast Reflex for Turn 1 & Step Transitions:
                                # Escalate immediately on life-threatening phrases or readiness confirmations
                                # without waiting 800-1200ms for AssemblyAI cloud silence timeout.
                                lowered_t = transcript_text.lower()
                                if not orchestrator.safety_coach.state.is_locked:
                                    has_emergency_signal = any(s in lowered_t for s in [
                                        "not breathing", "stopped breathing", "collapsed", "unresponsive",
                                        "no pulse", "barely breathing", "passed out", "fell down",
                                        "heart attack", "blue lips", "gasping", "can't breathe", "cant breathe",
                                        "is not breathing", "isn't breathing", "unconscious", "dying",
                                        "seizure", "convulsing", "overdose", "narcan", "naloxone", "fentanyl",
                                        "choking", "bleeding out", "stabbed", "shot", "cardiac arrest"
                                    ])
                                    if has_emergency_signal:
                                        logger.info(f"⚡ [Agent #1 Fast Reflex on Interim]: '{transcript_text}'")
                                        is_final = True
                                    else:
                                        continue
                                elif orchestrator.safety_coach.state.current_step_index < 2:
                                    # Fast advance for Step 1 -> Step 2 -> Step 3
                                    has_advance_signal = any(w in lowered_t.split() for w in [
                                        "ready", "done", "placed", "next", "ok", "okay",
                                        "start", "started", "push", "cpr", "go", "begin", "compress"
                                    ]) or any(p in lowered_t for p in ["hands placed", "ready to compress", "start cpr"])
                                    if has_advance_signal:
                                        logger.info(f"⚡ [Safety Coach Fast Reflex on Interim]: '{transcript_text}'")
                                        is_final = True
                                    else:
                                        continue
                                else:
                                    # During active CPR:
                                    # 110 BPM metronome clicks (every 545ms) prevent AssemblyAI cloud from seeing 800ms silence.
                                    # Fast Reflex for Panic FAQs, Questions, and Paramedic Arrival directly on Interims!
                                    is_cpr_panic_or_question = any(q in lowered_t for q in [
                                        "rib", "crack", "pop", "break", "broke",
                                        "sued", "legal", "liability",
                                        "vomit", "throw up", "chok",
                                        "never", "don't know", "dont know", "untrained",
                                        "tired", "exhaust", "burn", "swap", "fatigue",
                                        "gasp", "breath", "noise", "sound", "alive", "dead",
                                        "ambulance", "paramedic", "ems", "medic", "eta", "where",
                                        "they are here", "help is here", "arrived", "on scene",
                                        "stop", "can i stop", "how long"
                                    ]) or ("?" in transcript_text)

                                    if is_cpr_panic_or_question and len(transcript_text.split()) >= 3:
                                        logger.info(f"⚡ [Agent #3 CPR Fast Reflex on Interim]: '{transcript_text}'")
                                        is_final = True
                                    else:
                                        continue

                            # 2. Final speech turn: Rescuer completed utterance -> Execute coordinated multi-agent pipeline
                            logger.info(f"🗣️ Transcribed [Turn Final]: \"{transcript_text}\"")
                            
                            res = await asyncio.to_thread(
                                process_rescue_utterance,
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
        finally:
            try:
                await aai_ws.close()
            except Exception:
                pass
            finally:
                if _active_aai_ws is aai_ws:
                    _active_aai_ws = None
    except Exception as e:
        logger.error(f"AssemblyAI connection error: {e}")
        await client_ws.send_json({"error": str(e)})
    finally:
        logger.info("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
