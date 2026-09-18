"""
Agent #1 Triage Package
Exports public interface for instant semantic emergency classification.
"""

from server.agents.triage.schemas import EmergencyIntent, TriageAction, TriageResult
from server.agents.triage.router import FastSemanticRouter
from server.agents.triage.agent import TriageAgent

__all__ = ["EmergencyIntent", "TriageAction", "TriageResult", "FastSemanticRouter", "TriageAgent"]
