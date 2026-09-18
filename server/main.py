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

app = FastAPI(title=config.APP_NAME, version=config.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

triage_agent = TriageAgent()
safety_coach = SafetyCoachAgent()
companion_agent = CompanionAgent()

import urllib.parse

# AssemblyAI v3 Streaming WebSocket endpoint (Universal-3.5 Pro) with Medical Emergency Word Boosting
MEDICAL_BOOST_TERMS = json.dumps([
    "sternum", "tourniquet", "femoral", "brachial", "agonal", 
    "naloxone", "epipen", "compressions", "defibrillator", "narcan",
    "unresponsive", "carotid", "c-spine", "anaphylaxis", "hemorrhage"
])
AAI_WS_URL = f"wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&word_boost={urllib.parse.quote(MEDICAL_BOOST_TERMS)}"

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "HEALTHY", "agents": ["Agent1_Triage", "Agent2_SafetyCoach", "Agent3_Companion"]}

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

@app.get("/api/test-dispatch")
async def trigger_test_cad_dispatch(
    intent: str = "CARDIAC_ARREST",
    location: str = "Niaz Baig, Lahore City, Pakistan",
    lat: float = 31.4775,
    lon: float = 74.2387
):
    """Trigger an immediate 911 CAD & mobile push dispatch test."""
    packet = trigger_emergency_dispatch(
        intent=intent,
        patient_type="ADULT",
        latitude=lat,
        longitude=lon,
        street_address=location
    )
    return {
        "status": "DISPATCH_TRIGGERED",
        "cad_incident_id": packet.get("cad_incident_id"),
        "location": packet.get("street_address"),
        "ntfy_result": packet.get("ntfy_result"),
        "packet": packet
    }

@app.get("/api/test-companion")
async def test_companion_qa(query: str = "I think I broke a rib, am I pressing too hard?"):
    """Quickly test Agent #3 panic micro-Q&A and Section 4 safety gating."""
    answer = companion_agent.process_utterance(
        query,
        active_intent=safety_coach.state.active_intent or EmergencyIntent.CARDIAC_ARREST,
        protocol_step=safety_coach.state.current_step_index + 1 if safety_coach.state.is_locked else 3,
        cpr_active=True,
        cad_dispatched=True
    )
    word_count = len(answer.split()) if answer else 0
    return {
        "query": query,
        "companion_answer": answer,
        "word_count": word_count,
        "passed_18_word_rule": word_count <= 18,
        "model": "Groq LPU (qwen/qwen3.8-27b)" if os.getenv("GROQ_API_KEY") else "Deterministic Reflex",
        "status": "MATCHED" if answer else "NO_MATCH"
    }

def process_rescue_utterance(
    text: str,
    location: Optional[str] = None,
    lat: float = 37.7749,
    lon: float = -122.4194
) -> dict:
    """
    Centralized rescue pipeline coordinating Agent #1, Agent #2, and Agent #3.
    Preserves continuous clinical context across multi-burst speech turns and incorporates location.
    """
    # 1. Agent #1: Triage Classification with location awareness
    triage_res = triage_agent.classify(text, location=location)

    # Accumulate critical situational context into safety coach state
    if triage_res.c_spine_risk:
        safety_coach.state.c_spine_risk = True
    if triage_res.is_agonal_breathing:
        safety_coach.state.agonal_breathing = True
    if triage_res.bystander_status != "UNKNOWN":
        safety_coach.state.bystander_status = triage_res.bystander_status
    if triage_res.detected_limb:
        safety_coach.state.detected_limb = triage_res.detected_limb

    # 2. Agent #2: Safety Coach progression & dispatch
    directive_event = None
    cad_dispatch = None
    aed_info = None
    handoff_card = None
    just_locked = False

    initial_step_index = safety_coach.state.current_step_index

    if triage_res.action == TriageAction.LOCK_PROTOCOL:
        if not safety_coach.state.is_locked or safety_coach.state.active_intent != triage_res.intent:
            just_locked = True
            cad_dispatch = trigger_emergency_dispatch(
                intent=triage_res.intent.value,
                patient_type=triage_res.patient_type.value,
                latitude=lat,
                longitude=lon,
                street_address=location
            )
            aed_info = find_nearest_aed(latitude=lat, longitude=lon)
            safety_coach.state.cad_dispatch = cad_dispatch
            safety_coach.state.aed_info = aed_info
            cad_id = cad_dispatch.get("cad_incident_id")
            directive_event = safety_coach.initialize_protocol(
                intent=triage_res.intent,
                patient_type=triage_res.patient_type,
                confidence=triage_res.confidence,
                c_spine_risk=safety_coach.state.c_spine_risk,
                agonal_breathing=safety_coach.state.agonal_breathing,
                bystander_status=safety_coach.state.bystander_status,
                detected_limb=safety_coach.state.detected_limb,
                cad_incident_id=cad_id
            )
        else:
            # Protocol already locked to this intent: check if user voice advances step or arrives EMS
            cad_dispatch = safety_coach.state.cad_dispatch
            aed_info = safety_coach.state.aed_info
            directive_event = safety_coach.process_rescuer_utterance(text)
            if not directive_event and not safety_coach.state.paramedics_arrived:
                directive_event = safety_coach.get_current_directive()
    elif safety_coach.state.is_locked:
        cad_dispatch = safety_coach.state.cad_dispatch
        aed_info = safety_coach.state.aed_info
        directive_event = safety_coach.process_rescuer_utterance(text)
        if not directive_event and not safety_coach.state.paramedics_arrived:
            directive_event = safety_coach.get_current_directive()
        # Retain locked protocol metadata in triage output so rescuer UI remains focused on active emergency
        if triage_res.intent == EmergencyIntent.UNKNOWN or triage_res.action == TriageAction.FALLBACK:
            triage_res.intent = safety_coach.state.active_intent
            triage_res.confidence = safety_coach.state.triage_confidence or 0.95
            triage_res.action = TriageAction.LOCK_PROTOCOL

    user_advanced_step = (safety_coach.state.current_step_index > initial_step_index)

    # 3. Agent #3: Companion Micro-Q&A & Emotional Grounding with Multi-Agent Resuscitation Context
    # Pre-CPR Guidance Lifecycle:
    # Step 1: 911 CAD dispatch alerted with GPS location (Agent 2 Directive)
    # Step 2: Patient Posture & Hand Placement (Agent 2 Directive)
    # Step 3: Compressions Loop (Countdown 3-2-1-PUSH! -> 110 BPM Metronome) -> AGENT 3 ACTIVATES!
    guidance_completed = (
        safety_coach.state.is_locked
        and (safety_coach.state.current_step_index >= 2)
    )

    is_cpr_active = (
        guidance_completed
        and (safety_coach.state.active_intent == EmergencyIntent.CARDIAC_ARREST)
    )

    companion_ans = None
    if safety_coach.state.paramedics_arrived:
        companion_ans = "The paramedics are in charge now. Step back and take a deep breath. You did everything right."
    elif not safety_coach.state.is_locked:
        # Before emergency is identified, companion handles triage/general queries
        companion_ans = companion_agent.process_utterance(
            text,
            active_intent=triage_res.intent,
            protocol_step=1,
            cpr_active=False
        )
    elif just_locked:
        # Turn 1: Triage just identified cardiac arrest. Agent #2 speaks Step 1 directive with 100% focus.
        companion_ans = None
    else:
        # Step 1, 2, 3+: Rescuer is under protocol.
        # If user spoke a pure advance affirmation ("done", "ready", "placed"), let Agent 2 guide next step.
        # If user asked any question or voiced doubt ("never done before", "crack", "vomit", "tired"), Agent #3 answers with live LLM / Doctor voice!
        is_pure_advance = user_advanced_step and not any(k in text.lower() for k in ["?", "what", "how", "where", "why", "can", "should", "did", "break", "crack", "never", "not", "sued", "hurt", "dying", "dead", "tired"])
        if not is_pure_advance:
            companion_ans = companion_agent.process_utterance(
                text,
                active_intent=safety_coach.state.active_intent or triage_res.intent,
                protocol_step=safety_coach.state.current_step_index + 1,
                cpr_active=is_cpr_active,
                cad_dispatched=bool(safety_coach.state.cad_dispatch),
                patient_type=safety_coach.state.patient_type or triage_res.patient_type
            )

    # 4. Paramedic Handoff Card generation if paramedics arrived
    if safety_coach.state.paramedics_arrived:
        if not safety_coach.state.handoff_card:
            _, elapsed, comps = safety_coach.check_fatigue_swap_status()
            safety_coach.state.handoff_card = companion_agent.generate_ems_handoff(
                intent=safety_coach.state.active_intent or triage_res.intent,
                confidence=safety_coach.state.triage_confidence or triage_res.confidence,
                patient_type=safety_coach.state.patient_type or triage_res.patient_type,
                cpr_duration_seconds=elapsed,
                total_compressions=comps,
                cpr_cycles=safety_coach.state.cpr_cycles_completed,
                c_spine_risk=safety_coach.state.c_spine_risk,
                agonal_breathing=safety_coach.state.agonal_breathing,
                bystander_status=safety_coach.state.bystander_status,
                aed_deployed=(safety_coach.state.active_intent == EmergencyIntent.CARDIAC_ARREST),
                cad_incident_id=safety_coach.state.cad_incident_id
            )
        handoff_card = safety_coach.state.handoff_card

    # Explicit Multi-Agent Lifecycle States:
    # Agent 1: ACTIVE (Triaging) -> LOCKED_AND_HANDED_OFF (Turn 1) -> CLOSED_HANDED_OFF (Steps 1, 2, 3+)
    # Agent 2: STANDBY -> ACTIVE (Steps 1, 2, 3+) -> CONCLUDED (Paramedics)
    # Agent 3: STANDBY (Turn 1) -> ACTIVE_GROQ_LLM (Resuscitation Q&A) -> INCIDENT_CONCLUDED
    if just_locked:
        agent_1_status = "LOCKED_AND_HANDED_OFF"
    elif safety_coach.state.is_locked:
        agent_1_status = "CLOSED_HANDED_OFF"
    else:
        agent_1_status = "ACTIVE_TRIAGING"

    if safety_coach.state.paramedics_arrived:
        agent_2_status = "PARAMEDICS_ARRIVED_LOCKED"
    elif safety_coach.state.is_locked:
        agent_2_status = f"ACTIVE_STEP_{safety_coach.state.current_step_index + 1}"
    else:
        agent_2_status = "STANDBY"

    if safety_coach.state.paramedics_arrived:
        agent_3_status = "INCIDENT_CONCLUDED"
    elif not safety_coach.state.is_locked:
        agent_3_status = "STANDBY_PRE_TRIAGE"
    elif just_locked:
        agent_3_status = "STANDBY_STEP_1_DIRECTIVE"
    else:
        agent_3_status = "ACTIVE_GROQ_LLM"

    companion_model = "Groq LPU (qwen/qwen3.8-27b)" if os.getenv("GROQ_API_KEY") else "Deterministic Reflex"

    return {
        "triage": triage_res,
        "directive": directive_event,
        "companion_answer": companion_ans,
        "cad_dispatch": cad_dispatch,
        "aed_info": aed_info,
        "handoff_card": handoff_card,
        "transcript": text,
        "agent_1_status": agent_1_status,
        "agent_2_status": agent_2_status,
        "agent_3_status": agent_3_status,
        "companion_model": companion_model
    }

@app.post("/api/triage")
async def evaluate_text_triage(data: dict):
    """Direct HTTP triage classification endpoint with location awareness."""
    text = data.get("text", "").strip()
    location = data.get("location")
    lat = float(data.get("lat", 37.7749))
    lon = float(data.get("lon", -122.4194))
    result = process_rescue_utterance(text, location=location, lat=lat, lon=lon)
    
    return {
        "triage": result["triage"].model_dump(), 
        "directive": result["directive"].model_dump() if result["directive"] else None,
        "companion_answer": result["companion_answer"],
        "cad_dispatch": result["cad_dispatch"],
        "aed_info": result["aed_info"],
        "handoff_card": result["handoff_card"].model_dump() if result["handoff_card"] else None,
        "transcript": text,
        "agent_1_status": result["agent_1_status"],
        "agent_2_status": result["agent_2_status"],
        "agent_3_status": result["agent_3_status"],
        "companion_model": result["companion_model"]
    }

@app.post("/api/reset")
async def reset_rescue_session():
    """Resets all agent states for a fresh simulation session."""
    triage_agent.reset()
    safety_coach.reset()
    return {"status": "RESET_SUCCESSFUL"}

@app.post("/api/safety_coach/advance")
async def advance_safety_directive():
    """Advance Safety Coach step."""
    directive = safety_coach.advance_step()
    return {"directive": directive.model_dump() if directive else None}


@app.post("/api/companion/qa")
async def handle_companion_qa(data: dict):
    """Direct Micro-Q&A endpoint."""
    query = data.get("query", "").strip()
    ans = companion_agent.process_utterance(
        query,
        active_intent=safety_coach.state.active_intent or EmergencyIntent.CARDIAC_ARREST,
        protocol_step=safety_coach.state.current_step_index + 1 if safety_coach.state.is_locked else 3,
        cpr_active=True,
        cad_dispatched=True
    )
    words = len(ans.split()) if ans else 0
    return {
        "answer": ans or "Keep pushing to the beat. Help is on the way.",
        "word_count": words,
        "model": "Groq LPU (qwen/qwen3.8-27b)" if os.getenv("GROQ_API_KEY") else "Deterministic Reflex"
    }

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
