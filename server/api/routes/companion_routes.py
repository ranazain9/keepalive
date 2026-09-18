"""
Companion & Micro-Q&A API Routes
Handles live Agent #3 panic queries, Groq LPU LLM generation, and Section 4 compliance.
"""

import os
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from server.services.orchestrator_service import RescueOrchestrator
from server.schemas.emergency import EmergencyIntent

class CompanionQueryRequest(BaseModel):
    query: str
    active_intent: Optional[str] = "CARDIAC_ARREST"
    protocol_step: Optional[int] = 3
    cpr_active: Optional[bool] = True

def make_companion_router(orchestrator: RescueOrchestrator) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["Companion Agent & Q&A"])

    @router.get("/test-companion")
    async def test_companion_qa(query: str = "I think I broke a rib, am I pressing too hard?"):
        """Quickly test Agent #3 panic micro-Q&A and Section 4 safety gating."""
        state = orchestrator.safety_coach.state
        answer = orchestrator.companion_agent.process_utterance(
            query,
            active_intent=state.active_intent or EmergencyIntent.CARDIAC_ARREST,
            protocol_step=state.current_step_index + 1 if state.is_locked else 3,
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

    @router.post("/companion/qa")
    async def companion_qa_post(payload: dict):
        """Direct Micro-Q&A endpoint supporting both legacy and new schemas."""
        query = payload.get("query", "").strip()
        state = orchestrator.safety_coach.state
        ans = orchestrator.companion_agent.process_utterance(
            query,
            active_intent=state.active_intent or EmergencyIntent.CARDIAC_ARREST,
            protocol_step=state.current_step_index + 1 if state.is_locked else 3,
            cpr_active=True,
            cad_dispatched=True
        )
        words = len(ans.split()) if ans else 0
        return {
            "answer": ans or "Keep pushing to the beat. Help is on the way.",
            "companion_answer": ans or "Keep pushing to the beat. Help is on the way.",
            "word_count": words,
            "passed_18_word_rule": words <= 18,
            "model": "Groq LPU (qwen/qwen3.8-27b)" if os.getenv("GROQ_API_KEY") else "Deterministic Reflex"
        }

    return router
