"""
Panic Micro-Q&A Retrieval Engine for Agent #3
Answers caller anxiety and tactical doubts with ultra-concise (<18 words) clinical guidance.
Zero delay to CPR compressions.
"""

import time
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

PANIC_FAQ_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "agent_identity",
        "patterns": [
            "agent 3", "agent three", "companion", "are you there", "can you hear me",
            "are you listening", "hello agent", "hello agent 3", "who are you", "talk to me", "agent"
        ],
        "answer": "I am Agent 3, right here with you. Tell me what is happening or ask anything."
    },
    {
        "id": "help_general",
        "patterns": [
            "will you help me", "can you help me", "please help me", "help me please",
            "i need help", "can someone help", "help us", "help me"
        ],
        "answer": "I am right here with you. Tell me what happened—are they awake and breathing?"
    },
    {
        "id": "good_samaritan_legal",
        "patterns": [
            "can i get sued for breaking ribs", "sued for breaking ribs",
            "can i get sued if i break his ribs", "can i get sued if i break ribs",
            "sued if i break ribs", "liable if i break ribs",
            "can i get sued", "will i get sued", "get sued", "sued", "lawsuit",
            "legal trouble", "liability", "am i liable", "legal risk", "go to jail", "can i get scotched",
            "can they sue me", "will they sue me", "can i be sued", "legal protection"
        ],
        "answer": "Good Samaritan laws protect you. You are legally protected when attempting emergency CPR."
    },
    {
        "id": "rib_cracking",
        "patterns": [
            "break a rib", "breaking ribs", "rib cracked", "heard a crack", "rib popping",
            "pressing too hard", "pushing too hard", "cracking", "rib cracking", "ribs cracking",
            "ribs are cracking", "feel ribs cracking", "cracking ribs", "bones cracking",
            "cracking sound", "chest cracking", "bone pop", "rib pop", "break ribs",
            "will i break ribs", "broken ribs", "break his ribs", "break her ribs", "ribs break", "rib",
            "lips cracking", "lip cracking", "hear cracking", "ribs broke", "did i break a rib",
            "i heard a crack in his chest", "did i break his rib", "crack in his chest", "crack in chest",
            "heard a crack in his chest", "i heard a crack"
        ],
        "answer": "A rib pop can happen during effective CPR. Do not stop. Keep pushing to the beat."
    },
    {
        "id": "technique_verification",
        "patterns": [
            "am i doing this right", "am i doing it right", "is this right", "am i pushing right",
            "doing it correctly", "am i doing okay", "is this correct", "doing right", "doing this correct",
            "am i doing good", "is this good", "how am i doing"
        ],
        "answer": "You are doing great. Keep hands centered, elbows locked, and push to the beat."
    },
    {
        "id": "what_to_do_next",
        "patterns": [
            "what do i do", "what should i do", "what's next", "what next", "what do i do now",
            "tell me what to do", "what now", "what is next", "help me what to do", "now what"
        ],
        "answer": "Keep doing chest compressions in center of chest. Focus on the 110 beat."
    },
    {
        "id": "confusion_guidance",
        "patterns": [
            "confused", "i am confused", "i'm confused", "im confused", "i don't understand",
            "dont understand", "what does that mean", "i am lost", "i'm lost", "im lost",
            "i don't know what you mean", "unsure", "not sure", "what do you mean"
        ],
        "answer": "Stay calm, I am guiding you. Hands in center of chest, lock elbows, and push to the beat."
    },
    {
        "id": "patient_alive_doubt",
        "patterns": [
            "is he dead", "is she dead", "is he alive", "is she alive", "is he going to die",
            "will he live", "is it working", "did he die", "is he gone", "am i saving him"
        ],
        "answer": "Do not give up. Compressions are pumping oxygen to their brain right now. Keep pushing."
    },
    {
        "id": "blood_fluid",
        "patterns": [
            "blood coming from mouth", "bleeding from mouth", "blood in mouth", "nosebleed", "coughing blood", "there is blood"
        ],
        "answer": "Wipe blood quickly from mouth, then continue chest compressions immediately without stopping."
    },
    {
        "id": "hand_placement",
        "patterns": ["where do my hands go", "hand placement", "where to put hands", "center of chest", "where do i press", "where to push", "how to place hands"],
        "answer": "Heel of your hand right in center of chest between nipples. Lock elbows straight."
    },
    {
        "id": "mouth_to_mouth",
        "patterns": ["mouth to mouth", "rescue breaths", "should i breathe", "do i give breaths", "breathe into mouth", "do i give rescue breaths"],
        "answer": "Hands-only CPR is just as effective for adults. Keep pushing continuously to the beat."
    },
    {
        "id": "exhaustion_stopping",
        "patterns": [
            "can i stop", "need a break", "so tired", "arms hurt", "am exhausted", "can i rest",
            "tired", "getting tired", "arms burning", "burning", "arms are getting tired", "cant push anymore"
        ],
        "answer": "Do not stop compressions. If another person is with you, swap rescuers without pausing."
    },
    {
        "id": "vomit_airway",
        "patterns": ["he is throwing up", "vomiting", "threw up", "throw up", "liquid in mouth", "vomit"],
        "answer": "Roll them onto their side quickly to clear mouth, then return to back immediately."
    },
    {
        "id": "aed_wet_surface",
        "patterns": ["wet ground", "water on chest", "rain", "puddle", "is aed safe in water"],
        "answer": "Dry victim chest with a towel or shirt before applying AED pads. It is safe."
    },
    {
        "id": "aed_pacemaker",
        "patterns": ["pacemaker", "lump on chest", "medical implant", "metal on chest"],
        "answer": "Place AED pad at least one inch away from visible pacemaker lump. Continue CPR."
    },
    {
        "id": "checking_pulse",
        "patterns": ["should i check pulse", "check pulse", "look for heartbeat", "feel a pulse"],
        "answer": "Do not waste time checking pulse. If unresponsive and not breathing, continue CPR immediately."
    },
    {
        "id": "tourniquet_pain",
        "patterns": ["hurts too much", "screaming in pain", "tourniquet too tight", "bleeding hurts"],
        "answer": "Tourniquets must hurt to work. Tighten until bright red spurting bleeding stops completely."
    },
    {
        "id": "expose_bare_chest",
        "patterns": ["take clothes off", "take his shirt off", "cut shirt", "remove clothes", "take off shirt", "bare chest", "clothes on"],
        "answer": "Expose the bare chest immediately so you can see where to place your hands."
    },
    {
        "id": "untrained_novice",
        "patterns": [
            "never done this", "never done before", "never done", "never did this", "never did cpr",
            "never done cpr", "don't know cpr", "dont know cpr", "not trained", "never trained",
            "first time", "it was my first time", "i don't know what to do", "i dont know what to do",
            "i have never done this", "never done it", "how to do cpr", "i don't know how",
            "i never", "never", "i've never done", "i have never", "i never did"
        ],
        "answer": "Don't panic, I will guide you. Heel on center of chest, lock elbows, and push to the beat."
    },
    {
        "id": "too_late_doubt",
        "patterns": ["is it too late", "too late", "been down too long", "how long has he been down", "is he already gone"],
        "answer": "Start compressions immediately. It is never too late to try to save their life."
    },
    {
        "id": "patient_moan_sound",
        "patterns": ["he groaned", "made a sound", "making noises", "he moved", "did he gasp", "he made a noise"],
        "answer": "Do not stop unless they push your hands away and breathe normally. Keep pushing."
    },
    {
        "id": "agonal_breathing_sound",
        "patterns": [
            "he's gasping", "he is gasping", "is he breathing again", "gasping",
            "weird sound", "groaning", "snoring sound", "gasping sound", "agonal breath"
        ],
        "answer": "Do not stop. Gasping is agonal breathing, not normal breathing. Keep pushing to the beat."
    },
    {
        "id": "paramedic_arrival_debrief",
        "patterns": [
            "the paramedics are here", "paramedics are here", "ems is here", "ambulance is here",
            "paramedics arrived", "ambulance arrived", "paramites are here", "paramites", "paramedic",
            "medics are here", "ambulance", "paramedic is here"
        ],
        "answer": "The paramedics are in charge now. Step back and take a deep breath. You did everything right."
    },
    {
        "id": "ambulance_dispatch_status",
        "patterns": ["did you call 911", "did you call an ambulance", "are paramedics coming", "where is the ambulance", "is help coming", "when are they coming"],
        "answer": "911 CAD dispatch has been alerted with your exact GPS location. Keep pushing hard."
    },
    {
        "id": "pressing_force",
        "patterns": ["am i pushing too hard", "pushing too hard", "pressing too hard", "too much pressure"],
        "answer": "Pushing at least two inches deep is necessary to pump blood. Keep pushing hard."
    }
]

# Phonetic & ASR normalization dictionary for emergency audio
ASR_CORRECTIONS = {
    "scotched": "sued",
    "scotched?": "sued?",
    "sue": "sued",
    "law suit": "lawsuit",
    "rips": "ribs",
    "rib's": "ribs",
    "lips": "ribs",
    "c p r": "cpr",
    "first-time": "first time",
    "throwing": "vomiting",
    "throw": "vomit",
    "freaking": "scared",
    "scare": "scared",
    "agent three": "agent 3",
}

FORBIDDEN_PHRASES = [
    "stop compressions", "stop cpr", "stop pushing", "stop the beat", "take a break"
]

def enforce_section_4_safety_gate(text: str) -> str:
    """
    Section 4 Clinical Safety Gate:
    1. Strictly bounds text length to <= 18 words.
    2. Enforces hard safety filter blocking any dangerous halting instructions.
    """
    if not text:
        return ""
    lowered = text.lower()
    for forbidden in FORBIDDEN_PHRASES:
        if forbidden in lowered and "do not stop" not in lowered and "paramedic" not in lowered:
            return "Do not stop compressions. Keep pushing hard and fast to the beat."
            
    words = text.strip().split()
    if len(words) <= 18:
        return text

    # If it was ending with "Push to the beat.", preserve clean ending within 18 words
    beat_suffix = ["Push", "to", "the", "beat."]
    if any(k in lowered for k in ["push to", "the beat", "beat"]):
        available_slots = 18 - len(beat_suffix)
        prefix = " ".join(words[:available_slots]).rstrip(",;:.")
        return f"{prefix}. Push to the beat."

    return " ".join(words[:18]).rstrip(",;:") + "."

@dataclass
class MicroQAResponse:
    question: str
    answer: str
    word_count: int
    matched_faq_id: str
    confidence: float
    latency_ms: float

class MicroQAEngine:
    def answer_panic_query(
        self,
        query: str,
        active_intent: Optional[str] = None,
        protocol_step: Optional[int] = None,
        cpr_active: bool = False,
        cad_dispatched: bool = False
    ) -> Optional[MicroQAResponse]:
        start_time = time.perf_counter()
        lowered = query.lower()
        
        # Apply ASR phonetic corrections (e.g. 'scotched' -> 'sued')
        normalized = lowered
        for err, fix in ASR_CORRECTIONS.items():
            normalized = re.sub(rf"\b{re.escape(err)}\b", fix, normalized)

        best_match = None
        highest_score = 0.0
        
        for faq in PANIC_FAQ_DATABASE:
            for pattern in faq["patterns"]:
                if pattern in normalized or pattern in lowered:
                    score = 1.0 + min(0.90, len(pattern) / 50.0)
                    if faq["id"] == "good_samaritan_legal" and any(k in normalized for k in ["sued", "sue", "lawsuit", "liable", "liability"]):
                        score += 0.50
                    if faq["id"] == "untrained_novice" and any(k in normalized for k in ["never done", "never did", "not trained", "dont know cpr", "don't know cpr", "never done cpr", "first time"]):
                        score += 0.60
                    if score > highest_score:
                        highest_score = score
                        best_match = faq
                else:
                    # Token overlap match (capped at 0.85 so exact phrases always win)
                    p_words = set(re.findall(r"\b[a-z]{3,}\b", pattern))
                    q_words = set(re.findall(r"\b[a-z]{3,}\b", normalized))
                    if p_words and q_words:
                        overlap = len(p_words & q_words) / len(p_words)
                        if overlap >= 0.65:
                            score = 0.65 + (overlap * 0.25)
                            if score > highest_score:
                                highest_score = score
                                best_match = faq

        # Context-aware CPR reassurance fallback if panic question asked during active resuscitation
        if (not best_match or highest_score < 0.60) and cpr_active:
            q_words = set(re.findall(r"\b[a-z]{3,}\b", normalized))
            if any(w in q_words for w in ["right", "good", "correct", "well", "okay", "fine"]):
                answer_text = "You are doing great. Keep hands centered and push two inches deep to the beat."
                faq_id = "technique_reassurance"
            elif any(w in q_words for w in ["what", "next", "now", "doing"]):
                answer_text = "Continue chest compressions in center of chest until AED pads arrive."
                faq_id = "cpr_progression_guidance"
            elif any(w in q_words for w in ["scared", "shaking", "panic", "worried", "please", "god", "help"]):
                answer_text = "I am right here with you. Take a deep breath and keep pushing to the beat."
                faq_id = "emotional_grounding"
            elif any(w in q_words for w in ["dead", "alive", "dying", "breathe", "breathing"]):
                answer_text = "Do not stop. Your compressions are pumping blood to their brain right now."
                faq_id = "patient_vital_reassurance"
            else:
                answer_text = "Stay focused on the rhythmic clicking. Lock elbows and push hard to the beat."
                faq_id = "cpr_rhythm_anchor"

            bounded_answer = enforce_section_4_safety_gate(answer_text)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return MicroQAResponse(
                question=query,
                answer=bounded_answer,
                word_count=len(bounded_answer.split()),
                matched_faq_id=faq_id,
                confidence=0.85,
                latency_ms=round(elapsed_ms, 2)
            )

        if not best_match or highest_score < 0.60:
            return None
            
        answer_raw = best_match["answer"]
        if best_match["id"] == "agent_identity":
            if cpr_active:
                answer_raw = "I am Agent 3, right here with you. Keep following the rhythm and push to the beat."
            else:
                answer_raw = "I am Agent 3, your companion. Tell me what is happening with the patient."
        elif best_match["id"] == "help_general":
            if cpr_active:
                answer_raw = "I am right here coaching you every second. Keep pushing to the beat."
            else:
                answer_raw = "I am right here with you. Tell me what happened—are they awake and breathing?"
        elif best_match["id"] == "what_to_do_next":
            if cpr_active:
                answer_raw = "Keep doing chest compressions in center of chest. Focus on the 110 beat."
            else:
                answer_raw = "Tell me what happened: is the person awake, breathing, or bleeding? Help is on the way."

        bounded_answer = enforce_section_4_safety_gate(answer_raw)
        word_count = len(bounded_answer.split())
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        return MicroQAResponse(
            question=query,
            answer=bounded_answer,
            word_count=word_count,
            matched_faq_id=best_match["id"],
            confidence=round(highest_score, 2),
            latency_ms=round(elapsed_ms, 2)
        )
