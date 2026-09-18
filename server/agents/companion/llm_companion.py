"""
Contextual LLM Engine for Agent #3 (Clinical Companion & Micro-Q&A)
Provides situational intelligence grounded in live Agent #1 and Agent #2 telemetry.
Supports Groq LPUs (<250ms), Gemini Flash (<500ms), and OpenAI with sub-1ms fallback.
"""

import os
import time
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from server.agents.companion.micro_qa_engine import MicroQAEngine, MicroQAResponse, enforce_section_4_safety_gate

logger = logging.getLogger("KeepAlive")

class ContextualLLMCompanion:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.micro_qa = MicroQAEngine()

    def generate_response(
        self,
        query: str,
        active_intent: Optional[str] = "CARDIAC_ARREST",
        protocol_step: Optional[int] = 3,
        cpr_active: bool = True,
        cad_dispatched: bool = True,
        compressions_delivered: int = 0,
        cpr_elapsed_seconds: float = 0.0,
        cad_unit_eta: str = "Medic-4 ETA 4 mins"
    ) -> Optional[MicroQAResponse]:
        start_time = time.perf_counter()

        # 1. Tier 1: Dynamic Contextual LLM Generation via Groq LPU (<300ms)
        groq_key = self.groq_key or os.getenv("GROQ_API_KEY", "").strip()
        if groq_key:
            llm_ans = self._call_groq(
                query=query,
                active_intent=active_intent,
                protocol_step=protocol_step,
                cpr_active=cpr_active,
                compressions=compressions_delivered,
                elapsed_sec=cpr_elapsed_seconds,
                cad_eta=cad_unit_eta
            )
            if llm_ans:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                bounded = enforce_section_4_safety_gate(llm_ans)
                logger.info(f"🤝 [Agent #3 Groq LLM] Generated in {elapsed_ms:.1f}ms: '{bounded}'")
                return MicroQAResponse(
                    question=query,
                    answer=bounded,
                    word_count=len(bounded.split()),
                    matched_faq_id="groq_lpu_qwen",
                    confidence=0.96,
                    latency_ms=round(elapsed_ms, 2)
                )

        gemini_key = self.gemini_key or os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key:
            llm_ans = self._call_gemini(query, active_intent, protocol_step, cpr_active)
            if llm_ans:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                bounded = enforce_section_4_safety_gate(llm_ans)
                logger.info(f"🤝 [Agent #3 Gemini LLM] Generated in {elapsed_ms:.1f}ms: '{bounded}'")
                return MicroQAResponse(
                    question=query,
                    answer=bounded,
                    word_count=len(bounded.split()),
                    matched_faq_id="gemini_contextual_llm",
                    confidence=0.90,
                    latency_ms=round(elapsed_ms, 2)
                )

        # 2. Tier 2: Instant sub-1ms deterministic reflex fallback
        reflex_match = self.micro_qa.answer_panic_query(
            query=query,
            active_intent=active_intent,
            protocol_step=protocol_step,
            cpr_active=cpr_active,
            cad_dispatched=cad_dispatched
        )
        return reflex_match

    def _call_groq(
        self,
        query: str,
        active_intent: Optional[str],
        protocol_step: Optional[int],
        cpr_active: bool,
        compressions: int,
        elapsed_sec: float,
        cad_eta: str
    ) -> Optional[str]:
        groq_key = self.groq_key or os.getenv("GROQ_API_KEY", "").strip()
        if not groq_key:
            return None

        system_instruction = (
            "You are Agent 3 (Clinical Companion) in KeepAlive, speaking as a calm, compassionate, and authoritative human emergency physician / paramedic.\n"
            f"RESCUE STATE: Protocol: {active_intent or 'CARDIAC_ARREST'} | Step: {protocol_step or 3} | CPR Active: {cpr_active} | CAD ETA: {cad_eta}\n"
            "STRICT CLINICAL RULES:\n"
            "1. Speak like a reassuring human doctor talking directly to a frightened rescuer. Never sound robotic or canned.\n"
            "2. If caller says they never did CPR, are untrained, or panic about not knowing how: Reassure them and give direct physical direction: Don't panic, I will guide you. Heel on center of chest, lock elbows, and push to the beat.\n"
            "3. If caller mentions paramedics or ambulance arrived, say: The paramedics are in charge now. Step back and take a deep breath. You did everything right.\n"
            "4. For any other doubt (cracking ribs, vomiting, tired, not waking up), provide genuine medical reassurance in under 18 words.\n"
            "5. Never tell the rescuer to stop compressions during CPR.\n"
            "6. Always end with: Push to the beat. (unless paramedics have arrived).\n"
            "7. Strict limit: Under 15 words total. Plain text only. No quotes, preambles, or markdown."
        )

        models_to_try = ["qwen/qwen3.8-27b", "groq/compound-mini"]

        for model in models_to_try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 30,
                "temperature": 0.65
            }

            try:
                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {groq_key}",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KeepAlive-Emergency-Agent/1.0"
                    }
                )
                with urllib.request.urlopen(req, timeout=2.0) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"].strip()
                    if content:
                        # Clean up formatting
                        content = content.replace('"', '').replace("'", "'").replace('’', "'").replace('—', '-').strip()
                        is_paramedic_done = any(k in content.lower() for k in ["paramedic", "paramedics", "took over", "everything right"])
                        if cpr_active and not is_paramedic_done and not content.lower().endswith("beat.") and not content.lower().endswith("beat"):
                            content = f"{content.rstrip('.')} Push to the beat."
                        return content
            except Exception as e:
                logger.warning(f"[Agent #3 Groq LLM] Model {model} attempt failed: {e}")
                continue

        return None

    def _call_gemini(self, query: str, active_intent: Optional[str], protocol_step: Optional[int], cpr_active: bool) -> Optional[str]:
        prompt = (
            f"You are Agent 3 in KeepAlive. Rescuer is doing CPR under {active_intent}. "
            f"Respond to '{query}' in 15 words or fewer. Never tell them to stop. "
            "Always end with 'Push to the beat.' Return only plain text."
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=1.0) as res:
                data = json.loads(res.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.warning(f"[Agent #3 Gemini LLM] Fallback triggered: {e}")
            return None
