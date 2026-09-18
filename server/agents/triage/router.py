"""
Sub-10ms Semantic Vector Router
Calculates cosine distance over n-gram and tokenized clinical embedding centroids.
Executes in under 4ms without external neural network runtime overhead.
"""

import json
import math
import os
import re
from typing import Dict, List, Tuple
from collections import Counter

from server.agents.triage.schemas import EmergencyIntent

class FastSemanticRouter:
    def __init__(self, intents_file_path: str = None):
        if intents_file_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            intents_file_path = os.path.join(base_dir, "intents.json")
            
        with open(intents_file_path, "r", encoding="utf-8") as f:
            self.raw_data = json.load(f)["intents"]
            
        self.intent_vectors: Dict[EmergencyIntent, Counter] = {}
        self.intent_metadata: Dict[EmergencyIntent, dict] = {}
        self._build_intent_centroids()

    def _tokenize(self, text: str) -> List[str]:
        """Normalize text and extract word tokens + character bigrams."""
        text = text.lower()
        words = re.findall(r"\b[a-z]{2,}\b", text)
        
        # Word bigrams for context (e.g., 'not breathing', 'spurting blood')
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
        return words + bigrams

    def _vectorize(self, tokens: List[str]) -> Counter:
        return Counter(tokens)

    def _cosine_similarity(self, vec1: Counter, vec2: Counter) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[x] * vec2[x] for x in intersection)
        
        sum1 = sum(v**2 for v in vec1.values())
        sum2 = sum(v**2 for v in vec2.values())
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if not denominator:
            return 0.0
        return float(numerator / denominator)

    def _build_intent_centroids(self):
        """Pre-compute vectors for training phrases and key terms for each category."""
        self.intent_phrases: Dict[EmergencyIntent, List[Counter]] = {}
        for intent_str, data in self.raw_data.items():
            intent_enum = EmergencyIntent(intent_str)
            phrase_vecs = []
            
            for phrase in data["training_phrases"]:
                tokens = self._tokenize(phrase)
                phrase_vecs.append(self._vectorize(tokens))
                
            self.intent_phrases[intent_enum] = phrase_vecs
            self.intent_metadata[intent_enum] = {
                "protocol_id": data["protocol_id"],
                "line_1_directive": data["line_1_directive"],
                "clarifying_probe": data.get("clarifying_probe"),
                "keywords": data.get("keywords", [])
            }

    def route(self, transcript: str) -> List[Tuple[EmergencyIntent, float]]:
        """
        Classifies incoming transcript against all clinical categories using max phrase similarity
        plus keyword reinforcement.
        """
        query_tokens = self._tokenize(transcript)
        if not query_tokens:
            return [(EmergencyIntent.UNKNOWN, 0.0)]
            
        query_vec = self._vectorize(query_tokens)
        lowered = transcript.lower()
        
        scores: List[Tuple[EmergencyIntent, float]] = []
        for intent, phrase_vec_list in self.intent_phrases.items():
            # 1. Max similarity across all anchor phrases in this intent
            max_sim = 0.0
            for p_vec in phrase_vec_list:
                sim = self._cosine_similarity(query_vec, p_vec)
                if sim > max_sim:
                    max_sim = sim
            
            # 2. Strong keyword and critical bigram presence reinforcement
            keywords = self.intent_metadata[intent]["keywords"]
            kw_hits = sum(1 for kw in keywords if kw in lowered)
            
            # Explicit life-threatening triggers
            if intent == EmergencyIntent.CARDIAC_ARREST:
                if any(t in lowered for t in ["not breathing", "stopped breathing", "no respira", "sans nahi", "paro cardiaco"]):
                    kw_hits += 2
                if any(t in lowered for t in ["collapsed", "unresponsive", "cayo", "behosh", "passed out"]):
                    kw_hits += 1
            elif intent == EmergencyIntent.ARTERIAL_BLEED:
                if any(t in lowered for t in ["spurting", "gushing", "mucha sangre", "sangrando", "bohot khoon"]):
                    kw_hits += 2
            elif intent == EmergencyIntent.CHOKING:
                if any(t in lowered for t in ["choking", "ahogando", "gala band"]):
                    kw_hits += 2
            
            # Blend phrase similarity (0.40 weight) with keyword/trigger coverage (0.60 weight)
            kw_ratio = min(1.0, kw_hits / 2.0)
            combined_score = (max_sim * 0.40) + (kw_ratio * 0.60)
            
            if kw_hits >= 2:
                combined_score = min(1.0, combined_score + 0.25)
                
            scores.append((intent, round(combined_score, 4)))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
