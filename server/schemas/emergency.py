"""
Central Schemas Package for KeepAlive Agents
Consolidates all data contracts, enums, and event models across all agents.
"""

from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Intent & Triage Enums
# ---------------------------------------------------------
class EmergencyIntent(str, Enum):
    CARDIAC_ARREST = "CARDIAC_ARREST"
    ARTERIAL_BLEED = "ARTERIAL_BLEED"
    CHOKING = "CHOKING"
    ANAPHYLAXIS = "ANAPHYLAXIS"
    OVERDOSE = "OVERDOSE"
    UNKNOWN = "UNKNOWN"

class PatientType(str, Enum):
    ADULT = "ADULT"
    CHILD = "CHILD"
    INFANT = "INFANT"

class TriageAction(str, Enum):
    LOCK_PROTOCOL = "LOCK_PROTOCOL"
    CLARIFY_PROBE = "CLARIFY_PROBE"
    FALLBACK = "FALLBACK"

# ---------------------------------------------------------
# Agent #1 Output Model
# ---------------------------------------------------------
class TriageResult(BaseModel):
    intent: EmergencyIntent = Field(..., description="Detected clinical emergency category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity confidence score")
    action: TriageAction = Field(..., description="Action to execute: LOCK_PROTOCOL, CLARIFY_PROBE, or FALLBACK")
    latency_ms: float = Field(..., description="Total execution time in milliseconds")
    protocol_id: str = Field(..., description="Target deterministic protocol identifier")
    line_1_directive: str = Field(..., description="Immediate spoken directive to play (~15ms cache)")
    clarifying_probe: Optional[str] = Field(None, description="Fast 1-second question if confidence is ambiguous")
    is_agonal_breathing: bool = Field(False, description="Flag indicating caller described agonal gasping/snoring")
    detected_limb: Optional[str] = Field(None, description="Localized anatomical limb for bleeding if mentioned")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords that reinforced the intent")
    patient_type: PatientType = Field(default=PatientType.ADULT, description="Detected patient physiology: ADULT, CHILD, or INFANT")
    panic_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Caller panic and distress index (0.0 to 1.0)")
    is_high_panic: bool = Field(default=False, description="Flag indicating high panic distress > 0.70")
    bystander_status: str = Field(default="UNKNOWN", description="Bystander context: ALONE, MULTIPLE_PRESENT, or UNKNOWN")
    c_spine_risk: bool = Field(default=False, description="True if trauma/fall suggests spinal injury risk")
    is_escalated: bool = Field(default=False, description="True if protocol was auto-escalated from a secondary emergency")
    detected_language: str = Field(default="en", description="Detected language code (en, es, ur/hi)")
    verified_location: Optional[str] = Field(None, description="Current GPS coordinates or resolved street address")
    conversation_context: str = Field(default="", description="Accumulated sliding-window context")

# ---------------------------------------------------------
# Safety Coach (Agent #2) Models
# ---------------------------------------------------------
class ProtocolState(str, Enum):
    IDLE = "IDLE"
    VERIFY_UNRESPONSIVE = "VERIFY_UNRESPONSIVE"
    CALL_911 = "CALL_911"
    POSITION_PATIENT = "POSITION_PATIENT"
    ACTIVE_COMPRESSIONS = "ACTIVE_COMPRESSIONS"
    FATIGUE_SWAP = "FATIGUE_SWAP"
    PARAMEDICS_ARRIVED = "PARAMEDICS_ARRIVED"

class DirectiveEvent(BaseModel):
    step_number: int = Field(default=1, description="Sequential protocol step number")
    directive_text: str = Field(default="", description="Spoken rescue instruction")
    verbatim_text: str = Field(default="", description="Alias for directive text")
    spoken_voice_text: str = Field(default="", description="Natural spoken voice text for audio synthesis")
    asset_id: str = Field(default="", description="Pre-rendered audio asset identifier")
    audio_cue: str = Field(default="", description="Audio cue ID")
    target_duration_sec: float = Field(default=3.0, description="Estimated duration in seconds")
    ducking_db: float = Field(default=-4.0, description="Ducking level in decibels for background audio (-4dB allows keeping rhythm)")
    bpm: int = Field(default=0, description="Metronome cadence in beats per minute")
    metronome_bpm: int = Field(default=0, description="Metronome BPM")
    metronome_freq_hz: int = Field(default=3000, description="Metronome tone frequency in Hz (3000Hz pierces human speech formants)")
    target_depth_inches: float = Field(default=0.0, description="Target compression depth in inches (2.0-2.4)")
    target_depth_cm: float = Field(default=0.0, description="Target compression depth in cm (5.0-6.0)")
    cadence_mode: str = Field(default="CONTINUOUS_110BPM", description="Cadence mode: CONTINUOUS_110BPM or CYCLE_30_2")
    should_swap_rescuer: bool = Field(default=False, description="True if 2-minute cycle reached and fatigue swap required")
    cpr_elapsed_seconds: float = Field(default=0.0, description="Total elapsed CPR duration in seconds")
    total_compressions: int = Field(default=0, description="Estimated total compressions delivered")
    latency_ms: float = Field(default=0.0, description="Generation latency in milliseconds")

    def model_post_init(self, __context: Any) -> None:
        if not self.verbatim_text and self.directive_text:
            self.verbatim_text = self.directive_text
        elif not self.directive_text and self.verbatim_text:
            self.directive_text = self.verbatim_text
        if not self.spoken_voice_text and self.directive_text:
            self.spoken_voice_text = self.directive_text
        if not self.asset_id and self.audio_cue:
            self.asset_id = self.audio_cue
        elif not self.audio_cue and self.asset_id:
            self.audio_cue = self.asset_id
        if self.metronome_bpm and not self.bpm:
            self.bpm = self.metronome_bpm
        elif self.bpm and not self.metronome_bpm:
            self.metronome_bpm = self.bpm

# ---------------------------------------------------------
# EMS Handoff & Dispatch Models
# ---------------------------------------------------------
class EMSHandoffCard(BaseModel):
    incident_id: str = Field(..., description="Unique emergency incident identifier")
    timestamp_utc: str = Field(default="", description="UTC timestamp of handoff creation")
    primary_intent: EmergencyIntent = Field(default=EmergencyIntent.CARDIAC_ARREST, description="Primary clinical intent")
    triage_confidence: float = Field(default=1.0, description="Triage confidence score")
    patient_type: PatientType = Field(default=PatientType.ADULT, description="Patient physiology: ADULT, CHILD, or INFANT")
    cpr_duration_seconds: float = Field(default=0.0, description="Total bystander CPR duration in seconds")
    total_compressions_delivered: int = Field(default=0, description="Estimated total chest compressions delivered")
    aha_cycles_completed: int = Field(default=0, description="Completed 2-minute CPR cycles")
    c_spine_trauma_risk: bool = Field(default=False, description="Flag for cervical spine trauma risk")
    agonal_breathing_detected: bool = Field(default=False, description="Flag for agonal gasping detection")
    bystander_status: str = Field(default="UNKNOWN", description="Bystander context at scene")
    aed_deployed: bool = Field(default=False, description="Flag if public access AED was deployed")
    spoken_handoff_summary: str = Field(default="", description="10-second verbal summary script for incoming paramedics")
    spoken_report: str = Field(default="", description="Alias for spoken handoff summary")

    def model_post_init(self, __context: Any) -> None:
        if not self.spoken_report and self.spoken_handoff_summary:
            self.spoken_report = self.spoken_handoff_summary
        elif not self.spoken_handoff_summary and self.spoken_report:
            self.spoken_handoff_summary = self.spoken_report
