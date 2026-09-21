"""
Agent #2: The Safety Coach Agent (AHA / ERC BLS Engine)
Deterministic sub-15ms life-saving directives, 110 BPM metronome synchronization,
AHA 2-minute rescuer fatigue swap alerts, and paramedic arrival triggers.
"""

import re
import time
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

from server.schemas.emergency import EmergencyIntent, PatientType, DirectiveEvent
from server.agents.safety_coach.protocols import CLINICAL_PROTOCOLS, DirectiveStep
from server.core.logger import logger

PARAMEDIC_ARRIVAL_TRIGGERS = [
    "paramedics are here", "paramedics arrived", "paramedics have arrived", "paramedic is here",
    "paramedic", "paramedics", "paramites are here", "paramites", "paramite",
    "pyramids are here", "pyramids arrived", "pyramids", "pyramid", "pyramid are here",
    "paramed", "peramedics", "peramedic", "para medics", "pair of medics", "para medic",
    "ambulance is here", "ambulance arrived", "ambulance has arrived", "ambulance",
    "ems is here", "ems arrived", "ems has arrived", "ems just arrived", "ems",
    "medics are here", "medics arrived", "medic is here",
    "first responders are here", "first responders arrived", "help is here", "help arrived",
    "police are here", "they are here now", "they just arrived"
]

@dataclass
class SafetyCoachState:
    session_id: str
    active_intent: Optional[EmergencyIntent] = None
    patient_type: PatientType = PatientType.ADULT
    current_step_index: int = 0
    cpr_cycles_completed: int = 0
    metronome_active: bool = False
    metronome_bpm: int = 0
    is_locked: bool = False
    paramedics_arrived: bool = False
    cpr_started_at: Optional[float] = None
    started_at: float = field(default_factory=time.time)
    triage_confidence: float = 1.0
    c_spine_risk: bool = False
    agonal_breathing: bool = False
    bystander_status: str = "UNKNOWN"
    detected_limb: Optional[str] = None
    cad_incident_id: Optional[str] = None
    cad_dispatch: Optional[Dict[str, Any]] = None
    aed_info: Optional[Dict[str, Any]] = None
    handoff_card: Optional[Any] = None

class SafetyCoachAgent:
    """
    Sub-15ms Deterministic Safety Coach.
    Manages clinical step progression, 110 BPM metronome, and 2-min fatigue swap loops.
    """
    def __init__(self, session_id: str = "default_session"):
        self.state = SafetyCoachState(session_id=session_id)

    def reset(self):
        """Resets the Safety Coach state for a fresh incident."""
        self.state = SafetyCoachState(session_id=self.state.session_id)
        logger.info("🛡️ [Safety Coach] State reset to IDLE.")

    def initialize_protocol(
        self,
        intent: EmergencyIntent,
        patient_type: PatientType = PatientType.ADULT,
        confidence: float = 1.0,
        c_spine_risk: bool = False,
        agonal_breathing: bool = False,
        bystander_status: str = "UNKNOWN",
        detected_limb: Optional[str] = None,
        cad_incident_id: Optional[str] = None
    ) -> DirectiveEvent:
        start_time = time.perf_counter()
        self.state.active_intent = intent
        self.state.patient_type = patient_type
        self.state.current_step_index = 0
        self.state.cpr_cycles_completed = 0
        self.state.is_locked = True
        self.state.paramedics_arrived = False
        self.state.cpr_started_at = None
        self.state.triage_confidence = confidence
        self.state.c_spine_risk = c_spine_risk
        self.state.agonal_breathing = agonal_breathing
        self.state.bystander_status = bystander_status
        self.state.detected_limb = detected_limb
        self.state.cad_incident_id = cad_incident_id
        
        event = self._get_current_directive_event(start_time)
        logger.info(f"🛡️ [Safety Coach] Initialized protocol: {intent.value} ({patient_type.value}) -> Step 1 in {event.latency_ms:.2f}ms")
        return event

    def get_current_directive(self) -> DirectiveEvent:
        """Returns the current active directive event without advancing."""
        return self._get_current_directive_event(time.perf_counter())

    def advance_step(self) -> Optional[DirectiveEvent]:
        """Advance to next directive step upon caller confirmation or timer milestone."""
        start_time = time.perf_counter()
        if not self.state.is_locked or not self.state.active_intent or self.state.paramedics_arrived:
            return None
            
        steps = self._get_protocol_steps()
        if self.state.current_step_index < len(steps) - 1:
            self.state.current_step_index += 1
            if self.state.current_step_index == len(steps) - 1 and steps[-1].target_metronome_bpm > 0:
                # Started compressions
                self.state.cpr_started_at = time.time()
        elif steps and steps[-1].is_terminal_loop:
            # Increment CPR cycle count
            self.state.cpr_cycles_completed += 1
            
        event = self._get_current_directive_event(start_time)
        logger.info(f"🛡️ [Safety Coach] Advanced to step {self.state.current_step_index + 1} (Cycles: {self.state.cpr_cycles_completed}) in {event.latency_ms:.2f}ms")
        return event

    def process_rescuer_utterance(self, transcript: str) -> Optional[DirectiveEvent]:
        """
        Check if user voice indicates readiness to advance or if paramedics arrived.
        """
        lowered = transcript.lower().strip()
        
        # 1. Paramedic Arrival Check
        if any(trigger in lowered for trigger in PARAMEDIC_ARRIVAL_TRIGGERS):
            return self.process_paramedic_arrival()
            
        # 2. Advance Step Affirmation Check
        if any(neg in lowered for neg in ["never", "not done", "haven't", "havent", "don't know", "dont know"]):
            return None

        advance_triggers = [
            "done", "ready", "okay", "ok", "next", "i did it", "got it", "placed",
            "start", "started", "starting", "push", "pushing", "cpr", "begin", "go",
            "compress", "compressing", "compressions", "pumping", "pump"
        ]
        words = set(re.findall(r"\b[a-z']+\b", lowered))
        if any(trigger in words for trigger in advance_triggers) or any(phrase in lowered for phrase in ["i did it", "got it", "hands placed", "ready to compress"]):
            return self.advance_step()
            
        return None

    def process_paramedic_arrival(self) -> DirectiveEvent:
        """Halts metronome and switches to handoff standby."""
        start_time = time.perf_counter()
        self.state.paramedics_arrived = True
        self.state.metronome_active = False
        self.state.metronome_bpm = 0
        
        _, elapsed, comp_count = self.check_fatigue_swap_status()
        
        logger.info("🚑 [Safety Coach] Paramedics arrived. Metronome halted. Preparing handoff.")
        return DirectiveEvent(
            step_number=99,
            directive_text="The paramedics are in charge now. Step back and take a deep breath. You did everything right.",
            spoken_voice_text="The paramedics are in charge now. Step back and take a deep breath. You did everything right.",
            audio_cue="ems_arrival_stepback",
            metronome_bpm=0,
            ducking_db=0.0,
            cpr_elapsed_seconds=elapsed,
            total_compressions=comp_count,
            latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2)
        )

    def check_fatigue_swap_status(self) -> Tuple[bool, float, int]:
        """
        Calculates CPR duration and checks if 2-minute (120s) AHA fatigue swap alert is reached.
        Returns (should_swap, elapsed_seconds, estimated_compressions).
        """
        if not self.state.cpr_started_at:
            return False, 0.0, 0
            
        elapsed = time.time() - self.state.cpr_started_at
        estimated_compressions = int(elapsed * (110.0 / 60.0))
        
        # Every 120 seconds (2 minutes), AHA recommends swapping rescuers
        should_swap = (elapsed >= 120.0 and (int(elapsed) % 120 <= 5))
        return should_swap, round(elapsed, 1), estimated_compressions

    def _get_protocol_steps(self) -> List[DirectiveStep]:
        intent_val = self.state.active_intent.value if self.state.active_intent else EmergencyIntent.CARDIAC_ARREST.value
        pt_val = self.state.patient_type.value if self.state.patient_type else PatientType.ADULT.value
        
        intent_map = CLINICAL_PROTOCOLS.get(intent_val, {})
        return intent_map.get(pt_val) or intent_map.get(PatientType.ADULT.value, [])

    def _get_current_directive_event(self, start_perf_time: float) -> DirectiveEvent:
        steps = self._get_protocol_steps()
        if not steps:
            return DirectiveEvent(
                step_number=1,
                directive_text="Don't panic. 911 CAD dispatch has been alerted with your exact GPS location. We need to start CPR immediately! Lay them flat on firm ground.",
                spoken_voice_text="Don't panic. 911 CAD dispatch has been alerted with your exact GPS location. We need to start CPR immediately! Lay them flat on firm ground.",
                audio_cue="cpr_adult_step1_call911",
                metronome_bpm=0,
                metronome_freq_hz=3000,
                ducking_db=-4.0,
                latency_ms=(time.perf_counter() - start_perf_time) * 1000.0
            )

        idx = min(self.state.current_step_index, len(steps) - 1)
        step = steps[idx]
        
        self.state.metronome_bpm = step.target_metronome_bpm
        self.state.metronome_active = (step.target_metronome_bpm > 0)
        
        should_swap, elapsed, comp_count = self.check_fatigue_swap_status()
        directive_str = step.instruction
        voice_str = step.spoken_voice_text
        
        if should_swap:
            directive_str = "⚠️ 2 MINUTES COMPLETED! If someone is with you, SWAP rescuers now without stopping compressions!"
            voice_str = "Two minutes completed! Swap rescuers now if someone is with you!"

        latency = (time.perf_counter() - start_perf_time) * 1000.0
        
        return DirectiveEvent(
            step_number=step.step_number,
            directive_text=directive_str,
            spoken_voice_text=voice_str,
            audio_cue=step.audio_cue_id,
            metronome_bpm=step.target_metronome_bpm,
            metronome_freq_hz=step.metronome_freq_hz,
            target_depth_inches=step.target_depth_inches,
            target_depth_cm=step.target_depth_cm,
            cadence_mode=step.cadence_mode,
            should_swap_rescuer=should_swap,
            cpr_elapsed_seconds=elapsed,
            total_compressions=comp_count,
            ducking_db=step.ducking_db,
            latency_ms=round(latency, 2)
        )
