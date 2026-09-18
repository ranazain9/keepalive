"""
Caller Panic & Distress Scoring Engine
Calculates multi-modal distress index (0.0 to 1.0) using:
1. Linguistic Terror Indicators & Critical Emergency Markers
2. Repetition & Panic Loops
3. Speech Velocity (Words Per Minute / WPM)
4. Raw Audio Acoustic RMS Energy & Peak Amplitude
5. Tension Decay Dynamics during guided CPR cycles
"""

import re
import math
import time
from typing import Optional, List

PANIC_MARKERS = [
    "oh god", "please help", "help me", "dying", "hurry", "scared", "can't breathe",
    "cant breathe", "oh no", "what do i do", "screaming", "blood everywhere", "jesus", 
    "somebody help", "freaking out", "panicking", "wake up please", "don't die", 
    "dont die", "choking to death", "turning blue", "unresponsive", "bleeding out"
]

class PanicAnalyzer:
    def __init__(self):
        self.cpr_start_time: Optional[float] = None
        self.completed_cycles: int = 0

    @staticmethod
    def calculate_linguistic_score(transcript: str) -> float:
        lowered = transcript.lower()
        words = re.findall(r"\b[a-z]{2,}\b", lowered)
        if not words:
            return 0.0
            
        score = 0.0
        
        # 1. Distress Marker Count
        for marker in PANIC_MARKERS:
            if marker in lowered:
                score += 0.22
                
        # 2. Exclamation & Repetition Loops (e.g., 'help help', 'hurry hurry')
        word_counts = {}
        for w in words:
            word_counts[w] = word_counts.get(w, 0) + 1
            if word_counts[w] >= 2 and w in ["help", "please", "god", "hurry", "wake", "fast"]:
                score += 0.20
                
        # 3. Punctuation & Vocal Strain
        if "!" in transcript:
            score += 0.15 * min(3, transcript.count("!"))
            
        # 4. Short fragmented panic bursts
        if 3 <= len(words) <= 8 and any(m in lowered for m in ["help", "dying", "collapsed", "blood", "breathe"]):
            score += 0.15
            
        return round(min(1.0, max(0.10, score)), 2)

    @staticmethod
    def calculate_wpm_score(word_count: int, duration_seconds: float) -> float:
        """
        Computes distress modifier from Speech Velocity (Words Per Minute).
        Normal conversational speech: 120-150 WPM.
        Panic speech (hyperventilating/rushing): > 180 WPM -> up to +0.25 distress.
        """
        if duration_seconds <= 0.2 or word_count <= 1:
            return 0.0
        wpm = (word_count / duration_seconds) * 60.0
        if wpm > 220:
            return 0.25
        elif wpm > 180:
            return 0.15
        elif wpm > 150:
            return 0.05
        return 0.0

    @staticmethod
    def calculate_acoustic_rms(pcm_bytes: bytes) -> float:
        """
        Computes Root Mean Square (RMS) energy from raw 16-bit PCM audio samples.
        Returns normalized 0.0 (silence) to 1.0 (loud screaming/shouting).
        """
        if not pcm_bytes or len(pcm_bytes) < 2:
            return 0.0
        
        count = len(pcm_bytes) // 2
        sum_squares = 0.0
        
        for i in range(0, len(pcm_bytes), 2):
            sample = int.from_bytes(pcm_bytes[i:i+2], byteorder="little", signed=True)
            sum_squares += (sample / 32768.0) ** 2
            
        rms = math.sqrt(sum_squares / count)
        # Normalized amplitude scaling: normal talking ~0.05-0.15, shouting/screaming >0.40
        return round(min(1.0, rms * 2.5), 2)

    def calculate_composite_panic(
        self,
        transcript: str,
        duration_seconds: float = 0.0,
        pcm_bytes: Optional[bytes] = None,
        cpr_cycles: int = 0
    ) -> float:
        """
        Combines linguistic markers, speech velocity, acoustic RMS, and CPR tension decay.
        """
        linguistic = self.calculate_linguistic_score(transcript)
        
        # Speech velocity contribution
        words = re.findall(r"\b[a-z]{2,}\b", transcript.lower())
        wpm_bonus = self.calculate_wpm_score(len(words), duration_seconds) if duration_seconds > 0 else 0.0
        
        # Acoustic loudness contribution
        acoustic_bonus = 0.0
        if pcm_bytes:
            rms = self.calculate_acoustic_rms(pcm_bytes)
            if rms > 0.35:
                acoustic_bonus = 0.20
            elif rms > 0.20:
                acoustic_bonus = 0.10

        base_panic = min(1.0, linguistic + wpm_bonus + acoustic_bonus)
        
        # Tension Decay: As the rescuer performs steady CPR cycles, distress naturally stabilizes
        if cpr_cycles > 0:
            decay_factor = max(0.40, 1.0 - (cpr_cycles * 0.12))
            base_panic *= decay_factor
            
        return round(min(1.0, max(0.05, base_panic)), 2)

    # Backwards-compatible class method
    @classmethod
    def calculate_panic_score(cls, transcript: str) -> float:
        return cls.calculate_linguistic_score(transcript)
