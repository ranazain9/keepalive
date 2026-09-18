import time
import re
from typing import Optional, List

from server.core.config import config
from server.core.logger import logger
from server.schemas.emergency import (
    EmergencyIntent,
    PatientType,
    TriageAction,
    TriageResult
)
from server.agents.triage.router import FastSemanticRouter
from server.agents.triage.patient_classifier import PatientClassifier
from server.agents.triage.panic_analyzer import PanicAnalyzer
from server.agents.triage.fuzzy_matcher import FuzzyMatcher
from server.agents.triage.context_detector import ContextDetector

class SlidingWindowMemory:
    """Retains trailing conversational speech across multi-burst pauses (8s window)."""
    def __init__(self, max_duration_sec: float = 8.0):
        self.max_duration = max_duration_sec
        self.history: List[tuple] = []  # (timestamp, text)

    def add_and_get_context(self, text: str) -> str:
        now = time.time()
        # Filter out expired segments
        self.history = [(t, s) for (t, s) in self.history if (now - t) <= self.max_duration]
        
        # Don't add duplicate immediate repetitions
        if not self.history or self.history[-1][1] != text:
            self.history.append((now, text))
            
        return " ".join(s for _, s in self.history)

    def clear(self):
        self.history.clear()

class TriageAgent:
    def __init__(self, router: Optional[FastSemanticRouter] = None):
        self.router = router or FastSemanticRouter()
        self.lock_threshold = config.triage.CONFIDENCE_LOCK_THRESHOLD
        self.ambiguous_threshold = config.triage.CONFIDENCE_AMBIGUOUS_THRESHOLD
        self.memory = SlidingWindowMemory()
        
        self.pending_probe_intent: Optional[EmergencyIntent] = None
        self.previous_locked_intent: Optional[EmergencyIntent] = None
        
        # Agonal breathing acoustic/verbal markers
        self.agonal_markers = [
            "gasping", "snoring", "grunting", "gasp", "strange sound",
            "gurgling", "weird breathing", "barely breathing", "agonal"
        ]
        
        # Limb localization markers for arterial bleeding
        self.limb_markers = {
            "right thigh": "RIGHT_THIGH",
            "left thigh": "LEFT_THIGH",
            "right leg": "RIGHT_LEG",
            "left leg": "LEFT_LEG",
            "right arm": "RIGHT_ARM",
            "left arm": "LEFT_ARM",
            "forearm": "FOREARM",
            "neck": "NECK_ALERT"
        }

    def reset(self):
        """Clears sliding window memory and active probe / intent tracking."""
        self.memory.clear()
        self.pending_probe_intent = None
        self.previous_locked_intent = None
        logger.info("🎯 [Triage Agent] Session memory reset.")

    def _check_agonal_breathing(self, text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in self.agonal_markers)

    def _detect_limb(self, text: str) -> Optional[str]:
        lowered = text.lower()
        for limb_phrase, canonical in self.limb_markers.items():
            if limb_phrase in lowered:
                return canonical
        return None

    def classify(self, transcript: str, location: Optional[str] = None) -> TriageResult:
        """
        Main entry point for Agent #1.
        Evaluates caller transcript, incorporates verified caller GPS / address location,
        and returns structured TriageResult with latency telemetry.
        """
        start_time = time.perf_counter()
        
        # 1. Phonetic & Fuzzy Noise Normalization
        normalized_transcript = FuzzyMatcher.normalize_transcript(transcript)
        
        # 2. Accumulate multi-burst sliding-window memory
        accumulated_context = self.memory.add_and_get_context(normalized_transcript)
        lowered_query = transcript.lower().strip()
        
        # 3. Situational Context Extraction (Bystanders, C-Spine Trauma, Language)
        bystander_status = ContextDetector.detect_bystander_status(accumulated_context)
        c_spine_risk = ContextDetector.detect_c_spine_risk(accumulated_context)
        detected_lang = ContextDetector.detect_language(accumulated_context)
        
        # 4. Ambiguity Probe Resolver: Check if caller is answering an active probe ('yes' / 'no')
        if self.pending_probe_intent:
            if any(w in lowered_query for w in ["no", "nope", "not moving", "he is not", "negative", "no respira"]):
                top_intent = self.pending_probe_intent
                top_confidence = 0.96
                self.pending_probe_intent = None
                logger.info(f"🎯 [Probe Resolved: Negative -> Confirmed Emergency] Intent: {top_intent}")
                return self._finalize_result(
                    top_intent, top_confidence, TriageAction.LOCK_PROTOCOL,
                    accumulated_context, start_time, is_agonal=False, detected_limb=None,
                    bystander_status=bystander_status, c_spine_risk=c_spine_risk, detected_lang=detected_lang,
                    verified_location=location
                )
            elif any(w in lowered_query for w in ["yes", "yeah", "yep", "breathing normally", "si"]):
                self.pending_probe_intent = None
                logger.info("🎯 [Probe Resolved: Positive -> Patient Breathing]")
                return self._finalize_result(
                    EmergencyIntent.UNKNOWN, 0.50, TriageAction.FALLBACK,
                    accumulated_context, start_time, is_agonal=False, detected_limb=None,
                    bystander_status=bystander_status, c_spine_risk=c_spine_risk, detected_lang=detected_lang,
                    custom_directive="Place patient in recovery position on their side. Monitor breathing until paramedics arrive."
                )

        # 5. Dynamic Protocol Escalation (e.g. choking victim collapses)
        is_escalated = False
        if self.previous_locked_intent:
            escalated, new_intent_str = ContextDetector.detect_protocol_escalation(
                accumulated_context, self.previous_locked_intent.value
            )
            if escalated:
                is_escalated = True
                top_intent = EmergencyIntent(new_intent_str)
                top_confidence = 0.98
                action = TriageAction.LOCK_PROTOCOL
                self.previous_locked_intent = top_intent
                logger.warning(f"🚨 [Protocol Escalation] Escalated from choking to {top_intent.value}")
                return self._finalize_result(
                    top_intent, top_confidence, action, accumulated_context,
                    start_time, is_agonal=False, detected_limb=None,
                    bystander_status=bystander_status, c_spine_risk=c_spine_risk,
                    is_escalated=is_escalated, detected_lang=detected_lang,
                    custom_directive="Choking victim has collapsed! Lower them to the floor and begin CPR chest compressions immediately."
                )

        # 6. Patient Physiology Classification (Adult vs Child vs Infant)
        patient_type, specialized_directive = PatientClassifier.classify_patient(accumulated_context)
        
        # 7. Caller Panic & Distress Scoring
        panic_score = PanicAnalyzer.calculate_panic_score(accumulated_context)
        is_high_panic = (panic_score >= 0.70)
        
        # 8. Agonal breathing and Limb localization
        is_agonal = self._check_agonal_breathing(accumulated_context)
        detected_limb = self._detect_limb(accumulated_context)
        
        # 9. Fast semantic vector similarity evaluation on accumulated context
        ranked_intents = self.router.route(accumulated_context)
        top_intent, top_confidence = ranked_intents[0]
        
        # 10. MARCH Compound Trauma Prioritization
        has_bleed = any(intent == EmergencyIntent.ARTERIAL_BLEED and conf >= 0.60 for intent, conf in ranked_intents)
        has_cardiac = any(intent == EmergencyIntent.CARDIAC_ARREST and conf >= 0.60 for intent, conf in ranked_intents)
        
        if has_bleed and has_cardiac:
            top_intent = EmergencyIntent.ARTERIAL_BLEED
            top_confidence = 0.95
            logger.warning("🚨 [MARCH Triage] Compound trauma detected: Massive bleeding prioritized over CPR.")

        # 11. Agonal breathing override
        if is_agonal and top_intent != EmergencyIntent.ARTERIAL_BLEED:
            top_intent = EmergencyIntent.CARDIAC_ARREST
            top_confidence = max(top_confidence, 0.92)

        # 12. Action determination based on clinical confidence thresholds
        probe_question = None
        if top_confidence >= self.lock_threshold:
            action = TriageAction.LOCK_PROTOCOL
            self.pending_probe_intent = None
            self.previous_locked_intent = top_intent
        elif top_confidence >= self.ambiguous_threshold:
            action = TriageAction.CLARIFY_PROBE
            self.pending_probe_intent = top_intent
            probe_question = self.router.intent_metadata.get(top_intent, {}).get(
                "clarifying_probe", "Is the patient breathing normally? Answer YES or NO."
            )
        else:
            action = TriageAction.FALLBACK
            top_intent = EmergencyIntent.UNKNOWN

        # 13. Context-Aware Directive Customization
        final_directive = specialized_directive
        if action == TriageAction.LOCK_PROTOCOL:
            if top_intent == EmergencyIntent.CARDIAC_ARREST:
                if bystander_status == "MULTIPLE_PRESENT":
                    final_directive = "Direct the person with you to call 911 and find an AED right now! You kneel beside the chest and start compressions."
                elif c_spine_risk:
                    final_directive = "Trauma warning: Do NOT twist neck! Perform jaw-thrust airway maneuver only, call 911 on speaker and start CPR."
                elif is_agonal and not specialized_directive:
                    final_directive = "Do not wait or stop! Gasping is agonal breathing, not normal breathing. Place heel of hand on center of chest and push immediately."
            elif top_intent == EmergencyIntent.ARTERIAL_BLEED:
                if detected_limb == "NECK_ALERT":
                    final_directive = "⚠️ CRITICAL WARNING: NEVER apply a tourniquet around the neck! Apply firm, direct two-handed pressure with a clean cloth only."
                elif detected_limb in ["RIGHT_THIGH", "LEFT_THIGH", "RIGHT_LEG", "LEFT_LEG"]:
                    limb_clean = detected_limb.replace("_", " ").lower()
                    final_directive = f"Call 911 on speaker now! Bleeding on {limb_clean} locked. Apply heavy direct pressure immediately. Prepare tourniquet 2 to 3 inches above wound."
                elif detected_limb in ["RIGHT_ARM", "LEFT_ARM", "FOREARM"]:
                    limb_clean = detected_limb.replace("_", " ").lower()
                    final_directive = f"Call 911 on speaker now! Bleeding on {limb_clean} locked. Apply continuous direct pressure. Place tourniquet high and tight on the upper arm."

        return self._finalize_result(
            top_intent, top_confidence, action, accumulated_context,
            start_time, is_agonal, detected_limb, patient_type,
            panic_score, is_high_panic, bystander_status, c_spine_risk,
            is_escalated, detected_lang, probe_question, final_directive,
            verified_location=location
        )

    def _finalize_result(
        self, intent: EmergencyIntent, confidence: float, action: TriageAction,
        context: str, start_time: float, is_agonal: bool, detected_limb: Optional[str],
        patient_type: PatientType = PatientType.ADULT, panic_score: float = 0.0,
        is_high_panic: bool = False, bystander_status: str = "UNKNOWN",
        c_spine_risk: bool = False, is_escalated: bool = False,
        detected_lang: str = "en", probe_question: Optional[str] = None,
        custom_directive: Optional[str] = None,
        verified_location: Optional[str] = None
    ) -> TriageResult:
        meta = self.router.intent_metadata.get(intent, {
            "protocol_id": "GENERAL_EMERGENCY_DISPATCH",
            "line_1_directive": "Call 911 immediately and place phone on speaker. Stay with the patient.",
            "clarifying_probe": "What is the primary emergency?",
            "keywords": []
        })

        line_1 = custom_directive or meta["line_1_directive"]
        
        # If verified location is known and protocol is locked, append location acknowledgment
        if action == TriageAction.LOCK_PROTOCOL and verified_location and ("Call 911" in line_1 or "911 CAD" in line_1):
            line_1 = f"{line_1} 911 alert transmitted for {verified_location}."
            
        matched_kws = [kw for kw in meta.get("keywords", []) if kw in context.lower()]
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            f"🎯 [Agent #1] Intent: {intent.value} ({confidence:.2f}) | Location: {verified_location or 'GPS Pending'} | "
            f"Patient: {patient_type.value} | Bystanders: {bystander_status} | C-Spine: {c_spine_risk} | Lang: {detected_lang} | Latency: {elapsed_ms:.2f}ms"
        )

        return TriageResult(
            intent=intent,
            confidence=confidence,
            action=action,
            latency_ms=round(elapsed_ms, 2),
            protocol_id=meta["protocol_id"],
            line_1_directive=line_1,
            clarifying_probe=probe_question or meta.get("clarifying_probe"),
            is_agonal_breathing=is_agonal,
            detected_limb=detected_limb,
            matched_keywords=matched_kws,
            patient_type=patient_type,
            panic_score=panic_score,
            is_high_panic=is_high_panic,
            bystander_status=bystander_status,
            c_spine_risk=c_spine_risk,
            is_escalated=is_escalated,
            detected_language=detected_lang,
            verified_location=verified_location,
            conversation_context=context
        )
