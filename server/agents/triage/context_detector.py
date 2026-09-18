"""
Context, Trauma & Escalation Detector for Agent #1
Sub-millisecond situational context analysis:
1. Bystander Helper Context (Alone vs Helpers Present)
2. Cervical Spine (C-Spine) Trauma Risk (falls, collisions, impact)
3. Protocol Escalation (e.g., choking victim collapsing)
4. Multi-Lingual Crisis Detection
"""

import re
from typing import Tuple

BYSTANDER_HELPER_PATTERNS = [
    "here with me", "is here with", "are here with", "brother is here", "sister is here",
    "mom is here", "dad is here", "friend is here", "coworker is here", "wife is here",
    "husband is here", "we are two", "there are two", "there are 2", "there are 3",
    "people are here", "someone help me call", "we have help", "standing next to me"
]

BYSTANDER_ALONE_PATTERNS = [
    "i'm alone", "im alone", "i am alone", "just me", "only me", "no one else",
    "by myself", "nobody here", "all alone"
]

TRAUMA_CSPINE_PATTERNS = [
    "stairs", "roof", "ladder", "balcony", "window", "height", "fell from", "fell down",
    "car crash", "accident", "motorcycle", "hit by car", "hit his head", "hit her head",
    "head trauma", "diving", "shallow water", "spine", "neck"
]

ESCALATION_CHOKING_TO_ARREST = [
    "passed out", "lost consciousness", "not breathing anymore", "turned purple",
    "went limp", "unresponsive now", "collapsed"
]

class ContextDetector:
    @staticmethod
    def detect_bystander_status(transcript: str) -> str:
        lowered = transcript.lower()
        if any(p in lowered for p in BYSTANDER_ALONE_PATTERNS):
            return "ALONE"
        if any(p in lowered for p in BYSTANDER_HELPER_PATTERNS):
            return "MULTIPLE_PRESENT"
        return "UNKNOWN"

    @staticmethod
    def detect_c_spine_risk(transcript: str) -> bool:
        lowered = transcript.lower()
        return any(p in lowered for p in TRAUMA_CSPINE_PATTERNS)

    @staticmethod
    def detect_protocol_escalation(transcript: str, previous_intent: str) -> Tuple[bool, str]:
        lowered = transcript.lower()
        if previous_intent in ["CHOKING", "ANAPHYLAXIS", "OVERDOSE"]:
            if any(p in lowered for p in ESCALATION_CHOKING_TO_ARREST):
                return True, "CARDIAC_ARREST"
        return False, previous_intent

    @staticmethod
    def detect_language(transcript: str) -> str:
        lowered = transcript.lower()
        spanish_markers = ["ayuda", "no respira", "sangre", "ahogando", "por favor", "inconsciente", "auxilio", "cayo", "padre", "madre"]
        urdu_hindi_markers = ["madad", "sans nahi", "khoon", "behosh", "bachao", "pani", "dawai", "gala"]
        
        if any(m in lowered for m in spanish_markers):
            return "es"
        if any(m in lowered for m in urdu_hindi_markers):
            return "ur/hi"
        return "en"
