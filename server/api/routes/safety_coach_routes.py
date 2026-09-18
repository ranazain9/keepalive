"""
Safety Coach API Routes
Handles manual protocol step progression and 110 BPM metronome cadence triggers.
"""

from fastapi import APIRouter
from server.services.orchestrator_service import RescueOrchestrator

def make_safety_coach_router(orchestrator: RescueOrchestrator) -> APIRouter:
    router = APIRouter(prefix="/api/safety_coach", tags=["Safety Coach Agent"])

    @router.post("/advance")
    async def advance_safety_protocol_step():
        """Manually advances the active clinical protocol step."""
        event = orchestrator.safety_coach.advance_step()
        return {
            "status": "STEP_ADVANCED" if event else "NO_CHANGE",
            "directive": event,
            "current_step": orchestrator.safety_coach.state.current_step_index + 1
        }

    return router
