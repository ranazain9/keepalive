"""
KeepAlive Rescue Orchestrator Service
Coordinates the multi-agent resuscitation lifecycle:
- Agent #1: Triage Classification & CAD Dispatch
- Agent #2: Safety Coach Protocol Directives & 110 BPM Metronome
- Agent #3: Clinical Companion (Groq LPU LLM & Micro-Q&A)
"""

import os
import re
import time
from typing import Optional, Dict, Any

from server.schemas.emergency import EmergencyIntent, TriageAction, PatientType, DirectiveEvent
from server.agents.triage.agent import TriageAgent
from server.agents.safety_coach.agent import SafetyCoachAgent, PARAMEDIC_ARRIVAL_TRIGGERS
from server.agents.companion.agent import CompanionAgent
from server.tools.dispatcher_tool import trigger_emergency_dispatch, find_nearest_aed
from server.core.logger import logger

class RescueOrchestrator:
    def __init__(self, session_id: str = "default_session"):
        self.session_id = session_id
        self.triage_agent = TriageAgent()
        self.safety_coach = SafetyCoachAgent(session_id=session_id)
        self.companion_agent = CompanionAgent(session_id=session_id)

    def reset(self):
        """Wipes active session state across all 3 agents so the system starts 100% fresh."""
        self.triage_agent.reset()
        self.safety_coach.reset()
        self.companion_agent = CompanionAgent(session_id=self.session_id)
        logger.info("🔄 [Orchestrator] Multi-agent session reset to IDLE across all 3 agents.")

    def process_utterance(
        self,
        text: str,
        location: Optional[str] = None,
        lat: float = 37.7749,
        lon: float = -122.4194
    ) -> Dict[str, Any]:
        """
        Coordinates Agent 1 (Triage) -> Agent 2 (Safety Coach) -> Agent 3 (Companion).
        Preserves continuous clinical context across turns and incorporates live GPS.
        Enforces strict lockdown when paramedics arrive.
        """
        lowered_text = text.lower().strip()

        # 0. Check if paramedics are arriving in this utterance
        is_paramedic_trigger = any(trigger in lowered_text for trigger in PARAMEDIC_ARRIVAL_TRIGGERS)

        # Case A: Incident already concluded previously -> STOP ANSWERING COMPLETELY!
        if self.safety_coach.state.paramedics_arrived and not is_paramedic_trigger:
            logger.info("🔒 [Orchestrator] Incident already concluded and handed off to EMS. Ignoring further audio/queries.")
            triage_res = self.triage_agent.classify(text, location=location)
            triage_res.action = TriageAction.FALLBACK
            return {
                "triage": triage_res,
                "directive": None,
                "companion_answer": None,
                "cad_dispatch": None,
                "aed_info": None,
                "handoff_card": None,
                "transcript": text,
                "agent_1_status": "CLOSED_HANDED_OFF",
                "agent_2_status": "PARAMEDICS_ARRIVED_LOCKED",
                "agent_3_status": "INCIDENT_CONCLUDED",
                "companion_model": "Muted"
            }

        # Case B: Paramedics arriving in this utterance -> Speak final reassurance, lock system, deliver handoff card
        if is_paramedic_trigger:
            self.safety_coach.process_paramedic_arrival()

            if not self.safety_coach.state.handoff_card:
                _, elapsed, comps = self.safety_coach.check_fatigue_swap_status()
                self.safety_coach.state.handoff_card = self.companion_agent.generate_ems_handoff(
                    intent=self.safety_coach.state.active_intent or EmergencyIntent.CARDIAC_ARREST,
                    confidence=self.safety_coach.state.triage_confidence or 1.0,
                    patient_type=self.safety_coach.state.patient_type or PatientType.ADULT,
                    cpr_duration_seconds=elapsed,
                    total_compressions=comps,
                    cpr_cycles=self.safety_coach.state.cpr_cycles_completed,
                    c_spine_risk=self.safety_coach.state.c_spine_risk,
                    agonal_breathing=self.safety_coach.state.agonal_breathing,
                    bystander_status=self.safety_coach.state.bystander_status,
                    aed_deployed=(self.safety_coach.state.active_intent == EmergencyIntent.CARDIAC_ARREST),
                    cad_incident_id=self.safety_coach.state.cad_incident_id
                )

            handoff_card = self.safety_coach.state.handoff_card
            cad_disp = self.safety_coach.state.cad_dispatch
            aed = self.safety_coach.state.aed_info

            # Locked handoff directive
            arrival_directive = DirectiveEvent(
                step_number=99,
                directive_text="The paramedics are in charge now. Step back and take a deep breath. You did everything right.",
                spoken_voice_text="The paramedics are in charge now. Step back and take a deep breath. You did everything right.",
                audio_cue="ems_arrival_stepback",
                metronome_bpm=0,
                ducking_db=0.0,
                latency_ms=0.05
            )

            # Preserve locked emergency triage state
            triage_res = self.triage_agent.classify(text, location=location)
            triage_res.intent = self.safety_coach.state.active_intent or EmergencyIntent.CARDIAC_ARREST
            triage_res.action = TriageAction.LOCK_PROTOCOL

            logger.info("🔒 [Orchestrator] Paramedics on scene: concluding directive and handoff card delivered.")

            return {
                "triage": triage_res,
                "directive": arrival_directive,
                "companion_answer": "The paramedics are in charge now. Step back and take a deep breath. You did everything right.",
                "cad_dispatch": cad_disp,
                "aed_info": aed,
                "handoff_card": handoff_card,
                "transcript": text,
                "agent_1_status": "CLOSED_HANDED_OFF",
                "agent_2_status": "PARAMEDICS_ARRIVED_LOCKED",
                "agent_3_status": "INCIDENT_CONCLUDED",
                "companion_model": "Groq LPU (qwen/qwen3.8-27b)" if os.getenv("GROQ_API_KEY") else "Deterministic Reflex",
                "reset_after_ans": False,
                "system_locked": True
            }

        # 1. Agent #1: Triage Classification with location awareness
        triage_res = self.triage_agent.classify(text, location=location)

        # Context accumulation into safety coach state
        if triage_res.c_spine_risk:
            self.safety_coach.state.c_spine_risk = True
        if triage_res.is_agonal_breathing:
            self.safety_coach.state.agonal_breathing = True
        if triage_res.bystander_status != "UNKNOWN":
            self.safety_coach.state.bystander_status = triage_res.bystander_status
        if triage_res.detected_limb:
            self.safety_coach.state.detected_limb = triage_res.detected_limb

        # 2. Agent #2: Safety Coach progression & dispatch
        directive_event = None
        cad_dispatch = None
        aed_info = None
        handoff_card = None
        just_locked = False
        initial_step_index = self.safety_coach.state.current_step_index

        if triage_res.action == TriageAction.LOCK_PROTOCOL:
            if not self.safety_coach.state.is_locked or self.safety_coach.state.active_intent != triage_res.intent:
                just_locked = True
                cad_dispatch = trigger_emergency_dispatch(
                    intent=triage_res.intent.value,
                    patient_type=triage_res.patient_type.value,
                    latitude=lat,
                    longitude=lon,
                    street_address=location
                )
                aed_info = find_nearest_aed(latitude=lat, longitude=lon)
                self.safety_coach.state.cad_dispatch = cad_dispatch
                self.safety_coach.state.aed_info = aed_info
                cad_id = cad_dispatch.get("cad_incident_id")
                directive_event = self.safety_coach.initialize_protocol(
                    intent=triage_res.intent,
                    patient_type=triage_res.patient_type,
                    confidence=triage_res.confidence,
                    c_spine_risk=self.safety_coach.state.c_spine_risk,
                    agonal_breathing=self.safety_coach.state.agonal_breathing,
                    bystander_status=self.safety_coach.state.bystander_status,
                    detected_limb=self.safety_coach.state.detected_limb,
                    cad_incident_id=cad_id
                )
            else:
                cad_dispatch = self.safety_coach.state.cad_dispatch
                aed_info = self.safety_coach.state.aed_info
                directive_event = self.safety_coach.process_rescuer_utterance(text)
                if not directive_event and not self.safety_coach.state.paramedics_arrived:
                    directive_event = self.safety_coach.get_current_directive()
        elif self.safety_coach.state.is_locked:
            cad_dispatch = self.safety_coach.state.cad_dispatch
            aed_info = self.safety_coach.state.aed_info
            directive_event = self.safety_coach.process_rescuer_utterance(text)
            if not directive_event and not self.safety_coach.state.paramedics_arrived:
                directive_event = self.safety_coach.get_current_directive()
            if triage_res.intent == EmergencyIntent.UNKNOWN or triage_res.action == TriageAction.FALLBACK:
                triage_res.intent = self.safety_coach.state.active_intent
                triage_res.confidence = self.safety_coach.state.triage_confidence or 0.95
                triage_res.action = TriageAction.LOCK_PROTOCOL

        user_advanced_step = (self.safety_coach.state.current_step_index > initial_step_index)
        entering_step_3 = (initial_step_index < 2 and self.safety_coach.state.current_step_index >= 2)
        is_cpr_active = (
            self.safety_coach.state.is_locked 
            and self.safety_coach.state.active_intent == EmergencyIntent.CARDIAC_ARREST
            and self.safety_coach.state.current_step_index >= 2
        )

        # 3. Agent #3: Companion Micro-Q&A & Groq LPU Doctor
        # STRICT RULE: When Agent 2 is guiding (Step 1, Step 2, step transitions, countdowns),
        # Agent 2's clinical directive MUST speak cleanly and exclusively!
        # Agent 3 MUST NOT work while Agent 2 is guiding!
        # Agent 3 only activates during active CPR downstrokes when caller has a question or panic doubt.
        is_question_or_panic = self._is_panic_query(text)
        lowered_text = text.lower()
        is_explicit_companion = any(k in lowered_text for k in [
            "agent 3", "agent three", "companion", "hello agent", "talk to me", "who are you", "are you there", "can you hear me"
        ])
        companion_ans = None

        # Agent 3 NEVER interrupts while Agent 2 is guiding positioning or countdowns:
        should_trigger_companion = (
            is_cpr_active
            and not user_advanced_step
            and not entering_step_3
            and (is_question_or_panic or is_explicit_companion)
        )

        if should_trigger_companion:
            companion_ans = self.companion_agent.process_utterance(
                text,
                active_intent=self.safety_coach.state.active_intent or triage_res.intent,
                protocol_step=self.safety_coach.state.current_step_index + 1,
                cpr_active=True,
                cad_dispatched=bool(self.safety_coach.state.cad_dispatch),
                patient_type=self.safety_coach.state.patient_type or triage_res.patient_type
            )
            # Preserve active directive without interrupting compressions
            directive_event = self.safety_coach.get_current_directive()
        else:
            companion_ans = None

        # 4. Paramedic Handoff Card
        if self.safety_coach.state.paramedics_arrived:
            if not self.safety_coach.state.handoff_card:
                _, elapsed, comps = self.safety_coach.check_fatigue_swap_status()
                self.safety_coach.state.handoff_card = self.companion_agent.generate_ems_handoff(
                    intent=self.safety_coach.state.active_intent or triage_res.intent,
                    confidence=self.safety_coach.state.triage_confidence or triage_res.confidence,
                    patient_type=self.safety_coach.state.patient_type or triage_res.patient_type,
                    cpr_duration_seconds=elapsed,
                    total_compressions=comps,
                    cpr_cycles=self.safety_coach.state.cpr_cycles_completed,
                    c_spine_risk=self.safety_coach.state.c_spine_risk,
                    agonal_breathing=self.safety_coach.state.agonal_breathing,
                    bystander_status=self.safety_coach.state.bystander_status,
                    aed_deployed=(self.safety_coach.state.active_intent == EmergencyIntent.CARDIAC_ARREST),
                    cad_incident_id=self.safety_coach.state.cad_incident_id
                )
            handoff_card = self.safety_coach.state.handoff_card

        # Explicit Lifecycle Statuses
        if just_locked or self.safety_coach.state.is_locked:
            agent_1_status = "CLOSED_HANDED_OFF"
        else:
            agent_1_status = "ACTIVE_TRIAGING"

        if self.safety_coach.state.paramedics_arrived:
            agent_2_status = "PARAMEDICS_ARRIVED_LOCKED"
        elif is_cpr_active:
            agent_2_status = "ACTIVE_CPR_110BPM"
        elif self.safety_coach.state.is_locked:
            agent_2_status = f"ACTIVE_STEP_{self.safety_coach.state.current_step_index + 1}"
        else:
            agent_2_status = "STANDBY"

        if self.safety_coach.state.paramedics_arrived:
            agent_3_status = "INCIDENT_CONCLUDED"
        elif not is_cpr_active:
            agent_3_status = "STANDBY (Agent 2 Guiding)"
        elif companion_ans:
            agent_3_status = "ACTIVE_QNA_RESPONDER"
        else:
            agent_3_status = "ACTIVE_CPR_PACING_COMPANION"

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

    def _is_panic_query(self, text: str) -> bool:
        """
        Determines if rescuer utterance is a genuine panic doubt, question, or FAQ
        that requires Agent #3 resuscitation companion answering.
        Suppresses countdown echoes and step advance affirmations.
        """
        if not text or not text.strip():
            return False
        lowered = text.lower().strip()

        # 1. Direct Question Mark
        if "?" in text:
            return True

        # 2. Exclude countdown echo and advance affirmations
        countdown_echo_phrases = [
            "3 2 1", "3... 2... 1", "push to the beat", "two inches", "at least 2 inches",
            "chest rise fully", "hard and fast", "heel of hand", "lock elbows",
            "hands placed", "ready to compress"
        ]
        if any(p in lowered for p in countdown_echo_phrases):
            return False

        words = set(re.findall(r"\b[a-z']+\b", lowered))
        affirmations = {
            "ready", "done", "placed", "next", "ok", "okay", "yes", "yeah",
            "push", "beat", "pushed", "pushing", "i'm", "im", "got", "it",
            "started", "starting", "compress", "compressing", "compressions", "to"
        }
        if words.issubset(affirmations):
            return False

        # 3. If not an echo or advance affirmation, any rescuer speech during CPR
        # (questions, doubts, confusion, panic, fatigue) is handled by Agent #3
        return True

