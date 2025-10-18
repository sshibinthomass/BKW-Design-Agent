"""
Conversation state management for the LLM Orchestrator system.
"""

import logging
from typing import Dict, Any
from .enums import ConversationPhase

logger = logging.getLogger(__name__)


class ConversationState:
    """Manages conversation state and beam specifications."""

    def __init__(self):
        self.beam_spec = {}
        self.phase = ConversationPhase.GATHERING
        self.last_behavior = None
        self.missing_fields = [
            "material",
            "length_mm",
            "load_n",
            "width_mm",
            "height_mm",
        ]  # All fields are required for analysis

    def update_beam_spec(self, updates: Dict[str, Any]):
        """Update beam specifications with new information."""
        self.beam_spec.update(updates)
        self._update_missing_fields()

    def _update_missing_fields(self):
        """Update list of missing required fields - ALL fields always required."""
        required_fields = [
            "material",
            "length_mm",
            "load_n",
            "width_mm",
            "height_mm",
        ]  # All fields are required for analysis
        self.missing_fields = [
            field
            for field in required_fields
            if field not in self.beam_spec or not self.beam_spec.get(field)
        ]

    def can_transition_to(self, new_phase: ConversationPhase) -> bool:
        """Enforce strict linear progression only."""
        valid_transitions = {
            ConversationPhase.GATHERING: [ConversationPhase.ANALYZING],
            ConversationPhase.ANALYZING: [ConversationPhase.HISTORY_RESULTS],
            ConversationPhase.HISTORY_RESULTS: [ConversationPhase.OPTIMIZING],
            ConversationPhase.OPTIMIZING: [ConversationPhase.COMPLETED],
            ConversationPhase.COMPLETED: [ConversationPhase.GATHERING],  # New beam only
        }
        return new_phase in valid_transitions.get(self.phase, [])

    def transition_to(self, new_phase: ConversationPhase):
        """Safely transition with validation."""
        if self.can_transition_to(new_phase):
            logger.debug(f"Phase transition: {self.phase.value} -> {new_phase.value}")
            self.phase = new_phase
        else:
            raise ValueError(
                f"Invalid transition: {self.phase.value} -> {new_phase.value}"
            )

    def is_complete_for_analysis(self):
        """Check if we have enough information for beam analysis."""
        self._update_missing_fields()  # Ensure fields are updated
        return len(self.missing_fields) == 0

    def to_dict(self):
        """Convert state to dictionary for JSON serialization."""
        return {
            "beam_spec": self.beam_spec,
            "phase": self.phase.value,
            "last_behavior": self.last_behavior,
            "missing_fields": self.missing_fields,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create ConversationState from dictionary."""
        state = cls()
        state.beam_spec = data.get("beam_spec", {})
        state.phase = ConversationPhase(data.get("phase", "gathering_info"))
        state.last_behavior = data.get("last_behavior")
        state.missing_fields = data.get("missing_fields", [])
        return state
