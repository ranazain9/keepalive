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

    @router.post("/start_cpr")
    async def force_start_cpr():
        """Immediately activates Step 3: 110 BPM CPR pacing and metronome cadence."""
        import time
        from server.schemas.emergency import EmergencyIntent
        if not orchestrator.safety_coach.state.is_locked:
            orchestrator.safety_coach.initialize_protocol(
                intent=EmergencyIntent.CARDIAC_ARREST,
                confidence=1.0
            )
        # Advance directly to Step 3 (index 2 = compressions at 110 BPM)
        orchestrator.safety_coach.state.current_step_index = 2
        orchestrator.safety_coach.state.cpr_started_at = time.time()
        orchestrator.safety_coach.state.metronome_active = True
        orchestrator.safety_coach.state.metronome_bpm = 110
        event = orchestrator.safety_coach.get_current_directive()
        return {
            "status": "CPR_STARTED",
            "directive": event,
            "current_step": 3
        }

    return router
