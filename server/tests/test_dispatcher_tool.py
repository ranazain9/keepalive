"""
Unit Tests for 911 CAD Dispatch and AED Radar Tools
"""

import unittest
from server.tools.dispatcher_tool import trigger_emergency_dispatch, find_nearest_aed

class TestDispatcherTool(unittest.TestCase):
    def test_cad_dispatch_echo_priority(self):
        cad = trigger_emergency_dispatch(intent="CARDIAC_ARREST", patient_type="ADULT")
        self.assertEqual(cad["status"], "DISPATCH_CONFIRMED")
        self.assertEqual(cad["priority_level"], "ECHO_PRIORITY_1")
        self.assertIn("Medic-4", cad["assigned_units"])
        self.assertEqual(cad["estimated_eta_text"], "4 minutes")

    def test_aed_radar_lookup(self):
        aed = find_nearest_aed(37.7749, -122.4194)
        self.assertEqual(aed["status"], "AED_LOCATED")
        self.assertLess(aed["distance_meters"], 100.0)
        self.assertIn("Elevator", aed["location_description"])

if __name__ == "__main__":
    unittest.main()
