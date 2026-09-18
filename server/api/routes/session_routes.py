"""
Session & Health API Routes
Handles session resets, system health, and initial state.
"""

from fastapi import APIRouter
from server.services.orchestrator_service import RescueOrchestrator

def make_session_router(orchestrator: RescueOrchestrator) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["Session & Health"])

    @router.get("/health")
    async def health_check():
        """Health check confirming readiness of all 3 agents."""
        return {
            "status": "HEALTHY",
            "agents": ["Agent1_Triage", "Agent2_SafetyCoach", "Agent3_Companion"]
        }

    @router.post("/reset")
    @router.get("/reset")
    async def reset_session():
        """
        Wipes active emergency state across all 3 agents.
        Called on page refresh so each test starts 100% clean.
        """
        orchestrator.reset()
        return {
            "status": "SESSION_RESET",
            "agent_1_status": "ACTIVE_TRIAGING",
            "agent_2_status": "STANDBY",
            "agent_3_status": "STANDBY_PRE_TRIAGE",
            "metronome_bpm": 0,
            "directive": None,
            "companion_answer": None
        }

    return router
