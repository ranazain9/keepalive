"""
Agent #3: The Companion Agent (AssemblyAI Voice Agent Bridge)
Handles real-time conversational micro-Q&A (<18 words), psychological grounding,
and automated paramedic EMS handoff generation.
"""

import os
import time
from typing import Optional, Dict, Any

from server.schemas.emergency import EmergencyIntent, PatientType, EMSHandoffCard
from server.agents.companion.micro_qa_engine import MicroQAEngine, MicroQAResponse, enforce_section_4_safety_gate
from server.agents.companion.llm_companion import ContextualLLMCompanion
from server.agents.companion.handoff_generator import EMSHandoffGenerator
from server.core.logger import logger

GROUNDING_PHRASES = {
    "confused": "Stay calm, I am guiding you. Hands in center of chest, lock elbows, push to the beat.",
    "lost": "I am right here with you. Look at their chest, lock elbows, and push to the beat.",
    "unsure": "You are doing it right. Keep your elbows straight and push to the beat.",
    "scared": "You are doing everything right. Stay focused on the rhythm. Help is on the way.",
    "i can't": "You CAN do this. You are keeping blood flowing to their brain right now.",
    "is he dead": "Do not give up. Compressions are keeping them alive. Push to the beat.",
    "hurry": "Paramedics have been dispatched. Keep pushing hard and fast.",
    "help me": "I am right here coaching you every second. Keep pushing to the beat.",
    "shaking": "Adrenaline is normal. Lock your elbows straight and push with your upper body.",
    "freaking out": "Breathe. Look at your hands on the chest. Push hard and fast.",
    "crying": "Take a deep breath. Focus on the clicking beat. You are doing amazing."
}

class CompanionAgent:
    def __init__(self, session_id: str = "default_companion_session", prefer_llm: bool = True):
        self.session_id = session_id
        self.prefer_llm = prefer_llm
        self.qa_engine = MicroQAEngine()
        self.llm_engine = ContextualLLMCompanion()
        self.handoff_generator = EMSHandoffGenerator()

    def process_utterance(
        self,
        transcript: str,
        active_intent: Optional[EmergencyIntent] = None,
        protocol_step: Optional[int] = None,
        cpr_active: bool = False,
        cad_dispatched: bool = False,
        patient_type: Optional[PatientType] = None,
        force_reflex: bool = False
    ) -> Optional[str]:
        """
        Evaluates caller question, panic expression, or tactical doubt.
        Context-aware: coordinates seamlessly with active clinical resuscitation state.
        Returns ultra-brief (<=18 words) calming clinical response.
        """
        if not transcript or not transcript.strip():
            return None

        lowered = transcript.lower().strip()

        # 1. Dynamic Contextual LLM Engine (Groq LPU / Gemini) if API key is provided and preferred
        groq_active = bool(self.llm_engine.groq_key or os.getenv("GROQ_API_KEY", "").strip())
        gemini_active = bool(self.llm_engine.gemini_key or os.getenv("GEMINI_API_KEY", "").strip())
        
        if self.prefer_llm and not force_reflex and (groq_active or gemini_active):
            llm_res = self.llm_engine.generate_response(
                query=transcript,
                active_intent=active_intent.value if active_intent else "CARDIAC_ARREST",
                protocol_step=protocol_step or 3,
                cpr_active=cpr_active,
                cad_dispatched=cad_dispatched
            )
            if llm_res:
                safe_resp = enforce_section_4_safety_gate(llm_res.answer)
                logger.info(f"🤝 [Companion LLM] Match: {llm_res.matched_faq_id} ({len(safe_resp.split())} words in {llm_res.latency_ms:.2f}ms)")
                return safe_resp

        # 2. Context-Aware Panic FAQ Retrieval (Sub-1ms high precision tactical & anxiety answers)
        qa_res: Optional[MicroQAResponse] = self.qa_engine.answer_panic_query(
            transcript,
            active_intent=active_intent.value if active_intent else None,
            protocol_step=protocol_step,
            cpr_active=cpr_active,
            cad_dispatched=cad_dispatched
        )
        if qa_res:
            safe_resp = enforce_section_4_safety_gate(qa_res.answer)
            logger.info(f"🤝 [Companion Micro-Q&A] Match: {qa_res.matched_faq_id} ({len(safe_resp.split())} words in {qa_res.latency_ms:.2f}ms)")
            return safe_resp

        # 3. Context-Aware Emotional Grounding for caller distress expressions
        grounding_triggers = [
            "confused", "lost", "unsure", "don't understand", "dont understand",
            "don't know", "dont know", "scared", "freaking out", "i can't",
            "can't do this", "shaking", "crying", "panic"
        ]
        for trigger in grounding_triggers:
            if trigger in lowered:
                if cpr_active:
                    grounding_map = {
                        "confused": "Stay calm, I am guiding you. Hands in center of chest, lock elbows, push to the beat.",
                        "lost": "I am right here with you. Look at their chest, lock elbows, and push to the beat.",
                        "unsure": "You are doing it right. Keep your elbows straight and push to the beat.",
                        "don't understand": "Stay calm, I will guide every step. Hands in center of chest, push to the beat.",
                        "dont understand": "Stay calm, I will guide every step. Hands in center of chest, push to the beat.",
                        "don't know": "Don't panic, I will guide you. Heel on center of chest, lock elbows, push to the beat.",
                        "dont know": "Don't panic, I will guide you. Heel on center of chest, lock elbows, push to the beat.",
                        "scared": "You are doing everything right. Stay focused on the rhythm. Help is on the way.",
                        "freaking out": "Breathe. Look at your hands on the chest. Push hard and fast.",
                        "i can't": "You CAN do this. You are keeping blood flowing to their brain right now.",
                        "can't do this": "You CAN do this. You are keeping blood flowing to their brain right now.",
                        "shaking": "Adrenaline is normal. Lock your elbows straight and push with your upper body.",
                        "crying": "Take a deep breath. Focus on the clicking beat. You are doing amazing.",
                        "panic": "Take a deep breath. Stay with the rhythmic clicking. You are saving their life."
                    }
                else:
                    grounding_map = {
                        "confused": "Take a breath. I am right here with you. Tell me if the person is awake or breathing.",
                        "lost": "I am with you. Look at the person right now. Are they awake or breathing?",
                        "unsure": "Take a breath. Look at the person: are they awake or breathing?",
                        "don't understand": "Take a breath. I am right here. Tell me if they are awake or breathing.",
                        "dont understand": "Take a breath. I am right here. Tell me if they are awake or breathing.",
                        "don't know": "Take a breath. Look at the chest. Is it rising and falling?",
                        "dont know": "Take a breath. Look at the chest. Is it rising and falling?",
                        "scared": "You are doing everything right. Take a breath and check if they are breathing.",
                        "freaking out": "Take a deep breath. I am with you. Tell me if they are awake.",
                        "i can't": "You can do this. Stay calm and tell me if they are breathing.",
                        "can't do this": "You can do this. Stay calm and tell me if they are breathing.",
                        "shaking": "Take a breath. Look at the person: are they awake or breathing?",
                        "crying": "Take a deep breath. I am with you. Tell me what is happening.",
                        "panic": "Take a deep breath. Stay calm. Tell me if the person is awake."
                    }
                resp = grounding_map.get(trigger, "I am right here with you. Help is on the way.")
                safe_resp = enforce_section_4_safety_gate(resp)
                logger.info(f"🤝 [Companion Grounding] Triggered: '{trigger}' -> '{safe_resp}'")
                return safe_resp

        # 4. Ultimate Clinical Failsafe (Offline Safety Boundary)
        if cpr_active:
            failsafe = "Do not stop compressions. Lock elbows straight and push hard to the beat."
            logger.info("🛡️ [Companion Safety Boundary] Emitted offline failsafe CPR anchor.")
            return enforce_section_4_safety_gate(failsafe)
        else:
            failsafe = "I am right here with you. Help is on the way. Focus on the patient."
            logger.info("🛡️ [Companion Safety Boundary] Emitted pre-CPR reassurance anchor.")
            return enforce_section_4_safety_gate(failsafe)

    def generate_ems_handoff(
        self,
        intent: EmergencyIntent,
        confidence: float,
        patient_type: PatientType,
        cpr_duration_seconds: float,
        total_compressions: int,
        cpr_cycles: int,
        c_spine_risk: bool = False,
        agonal_breathing: bool = False,
        bystander_status: str = "UNKNOWN",
        aed_deployed: bool = False,
        cad_incident_id: Optional[str] = None
    ) -> EMSHandoffCard:
        """
        Compiles and returns the clinical EMS Handoff Card and verbal briefing.
        """
        card = self.handoff_generator.generate_handoff_card(
            session_id=self.session_id,
            intent=intent,
            confidence=confidence,
            patient_type=patient_type,
            cpr_duration_seconds=cpr_duration_seconds,
            total_compressions=total_compressions,
            cpr_cycles=cpr_cycles,
            c_spine_risk=c_spine_risk,
            agonal_breathing=agonal_breathing,
            bystander_status=bystander_status,
            aed_deployed=aed_deployed,
            cad_incident_id=cad_incident_id
        )
        logger.info(f"🚑 [Companion Agent] Generated EMS Handoff Card: {card.incident_id}")
        return card
