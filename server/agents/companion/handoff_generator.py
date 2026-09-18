"""
Automated Paramedic EMS Handoff Report Generator
Generates clinical JSON EMSHandoffCard and 10-second spoken report
upon ambulance / EMS arrival.
"""

import time
from typing import Dict, Any, Optional
from server.schemas.emergency import EMSHandoffCard, EmergencyIntent, PatientType

class EMSHandoffGenerator:
    @staticmethod
    def generate_handoff_card(
        session_id: str,
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
        Synthesizes clinical EMS card and 10-second handover verbal script.
        """
        mins = int(cpr_duration_seconds // 60)
        secs = int(cpr_duration_seconds % 60)
        time_str = f"{mins} min {secs} sec" if mins > 0 else f"{secs} seconds"

        # 10-second spoken handover script for paramedics
        spoken_parts = [
            f"EMS Handoff: {patient_type.value} patient with {intent.value.replace('_', ' ').title()}.",
            f"Bystander CPR performed for {time_str}, approximately {total_compressions} compressions delivered at 110 BPM."
        ]
        
        if c_spine_risk:
            spoken_parts.append("Trauma caution: Mechanism of injury indicates potential cervical spine risk.")
        if agonal_breathing:
            spoken_parts.append("Initial presentation included agonal gasping.")
        if aed_deployed:
            spoken_parts.append("Public access AED was deployed.")

        spoken_report = " ".join(spoken_parts)

        return EMSHandoffCard(
            incident_id=cad_incident_id or f"CAD-{int(time.time())}",
            timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            primary_intent=intent,
            triage_confidence=confidence,
            patient_type=patient_type,
            cpr_duration_seconds=round(cpr_duration_seconds, 1),
            total_compressions_delivered=total_compressions,
            aha_cycles_completed=cpr_cycles,
            c_spine_trauma_risk=c_spine_risk,
            agonal_breathing_detected=agonal_breathing,
            bystander_status=bystander_status,
            aed_deployed=aed_deployed,
            spoken_handoff_summary=spoken_report
        )
