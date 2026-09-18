"""
Dispatch & AED API Routes
Handles 911 CAD incident packet transmission and live OpenStreetMap AED lookup.
"""

from fastapi import APIRouter
from server.tools.dispatcher_tool import trigger_emergency_dispatch

def make_dispatch_router() -> APIRouter:
    router = APIRouter(prefix="/api", tags=["Dispatch & AED"])

    @router.get("/test-dispatch")
    async def trigger_test_cad_dispatch(
        intent: str = "CARDIAC_ARREST",
        location: str = "Niaz Baig, Lahore City, Pakistan",
        lat: float = 31.4775,
        lon: float = 74.2387
    ):
        """Trigger an immediate 911 CAD & mobile push dispatch test."""
        packet = trigger_emergency_dispatch(
            intent=intent,
            patient_type="ADULT",
            latitude=lat,
            longitude=lon,
            street_address=location
        )
        return {
            "status": "DISPATCH_TRIGGERED",
            "cad_incident_id": packet.get("cad_incident_id"),
            "location": packet.get("street_address"),
            "ntfy_result": packet.get("ntfy_result"),
            "packet": packet
        }

    return router
