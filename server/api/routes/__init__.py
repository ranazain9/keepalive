"""
KeepAlive API Routes Package
Exports router factory functions for modular backend assembly.
"""

from server.api.routes.session_routes import make_session_router
from server.api.routes.triage_routes import make_triage_router
from server.api.routes.safety_coach_routes import make_safety_coach_router
from server.api.routes.companion_routes import make_companion_router
from server.api.routes.dispatch_routes import make_dispatch_router

__all__ = [
    "make_session_router",
    "make_triage_router",
    "make_safety_coach_router",
    "make_companion_router",
    "make_dispatch_router"
]
