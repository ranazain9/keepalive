"""
Patient Physiology & Age Classifier
Detects whether patient is an INFANT, CHILD, or ADULT and adapts CPR mechanics.
"""

import re
from typing import Tuple
from server.schemas.emergency import PatientType

INFANT_MARKERS = [
    "baby", "infant", "newborn", "neonatal", "months old", "month old", "six month",
    "few weeks old", "nursery", "crib"
]

CHILD_MARKERS = [
    "child", "kid", "toddler", "boy", "girl", "son", "daughter",
    "years old", "year old", "elementary", "kindergarten", "school"
]

class PatientClassifier:
    @staticmethod
    def classify_patient(transcript: str) -> Tuple[PatientType, str]:
        """
        Analyzes speech transcript for physiological age markers.
        Returns (PatientType, specialized_directive_override)
        """
        lowered = transcript.lower()
        
        # 1. Check for Infant markers
        for marker in INFANT_MARKERS:
            if marker in lowered:
                # Check for year exclusions (e.g. '15 years old son' is child/adult, not baby)
                if not re.search(r"\b(1[0-9]|[2-9][0-9])\s*year", lowered):
                    return (
                        PatientType.INFANT,
                        "Call 911 on speaker now! For an infant, use two fingers or two thumbs in the center of the chest. Push down 1.5 inches to the beat."
                    )
                    
        # 2. Check for Child markers (approx. 1 to 8 years)
        for marker in CHILD_MARKERS:
            if marker in lowered:
                # Check if it's explicitly a teen or adult child
                age_match = re.search(r"\b(\d+)\s*year", lowered)
                if age_match:
                    age = int(age_match.group(1))
                    if age < 1:
                        return (
                            PatientType.INFANT,
                            "Call 911 on speaker now! For an infant, use two fingers in the center of the chest. Push down 1.5 inches."
                        )
                    elif age <= 12:
                        return (
                            PatientType.CHILD,
                            "Call 911 on speaker now! For a child, use the heel of one hand in the center of the chest. Push down 2 inches to the beat."
                        )
                else:
                    return (
                        PatientType.CHILD,
                        "Call 911 on speaker now! For a child, use the heel of one hand in the center of the chest. Push down 2 inches to the beat."
                    )
                    
        # 3. Default to Adult
        return (PatientType.ADULT, "")
