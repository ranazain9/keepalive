"""
Unit Tests for Automated Paramedic EMS Handoff Generation
"""

import unittest
from server.agents.companion.handoff_generator import EMSHandoffGenerator
from server.schemas.emergency import EmergencyIntent, PatientType

class TestEMSHandoff(unittest.TestCase):
    def test_ems_handoff_card_generation(self):
        card = EMSHandoffGenerator.generate_handoff_card(
            session_id="test_session_123",
            intent=EmergencyIntent.CARDIAC_ARREST,
            confidence=0.98,
            patient_type=PatientType.ADULT,
            cpr_duration_seconds=185.0,
            total_compressions=340,
            cpr_cycles=2,
            c_spine_risk=True,
            agonal_breathing=True,
            bystander_status="MULTIPLE_PRESENT",
            aed_deployed=True
        )

        self.assertEqual(card.primary_intent, EmergencyIntent.CARDIAC_ARREST)
        self.assertEqual(card.patient_type, PatientType.ADULT)
        self.assertEqual(card.total_compressions_delivered, 340)
        self.assertEqual(card.aha_cycles_completed, 2)
        self.assertTrue(card.c_spine_trauma_risk)
        self.assertTrue(card.agonal_breathing_detected)
        self.assertTrue(card.aed_deployed)
        
        # Verify spoken summary exists and contains essential metrics
        self.assertIn("3 min 5 sec", card.spoken_handoff_summary)
        self.assertIn("340 compressions", card.spoken_handoff_summary)
        self.assertIn("cervical spine", card.spoken_handoff_summary)

if __name__ == "__main__":
    unittest.main()
