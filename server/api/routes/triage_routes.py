"""
Triage & Rescue Stream API Routes
Handles caller emergency speech classification, CAD dispatch, and directive progression.
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from server.services.orchestrator_service import RescueOrchestrator

class TriageRequest(BaseModel):
    text: str
    location: Optional[str] = None
    lat: Optional[float] = 37.7749
    lon: Optional[float] = -122.4194

def make_triage_router(orchestrator: RescueOrchestrator) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["Triage & Resuscitation"])

    @router.post("/triage")
    @router.post("/rescue-stream")
    async def triage_rescue_utterance(payload: TriageRequest):
        """
        Processes rescuer speech turn.
        Coordinates Agent 1 (Triage) -> Agent 2 (Safety Coach) -> Agent 3 (Companion).
        """
        res = orchestrator.process_utterance(
            text=payload.text,
            location=payload.location,
            lat=payload.lat,
            lon=payload.lon
        )
        res["is_final"] = True
        return res

    return router
