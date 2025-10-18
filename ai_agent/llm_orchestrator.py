"""
LLM Orchestrator - Main conversation flow controller for GenDesign
Handles routing user input to appropriate AI behaviors and manages conversation state.
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from anthropic import Anthropic

from .enums import ConversationPhase
from .conversation_state import ConversationState
from .beam_processor import BeamProcessor
from .intent_detector import IntentDetector
from .historical_analyzer import HistoricalAnalyzer
from .visualization_handler import VisualizationHandler
from .phase_handlers import PhaseHandlers

# Set logging level based on environment
LOG_LEVEL = logging.DEBUG if os.getenv("FLASK_ENV") == "development" else logging.INFO

# Configure logging to both console and file
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("logs/gendesign.log", mode="a"),  # File output
    ],
)

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """Main conversation flow controller for GenDesign."""

    def __init__(self, anthropic_api_key: str):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.conversation_states = {}  # session_id -> ConversationState

        # Initialize modular components
        self.beam_processor = BeamProcessor(self.client)
        self.intent_detector = IntentDetector(self.client)
        self.historical_analyzer = HistoricalAnalyzer()
        self.visualization_handler = VisualizationHandler()
        self.phase_handlers = PhaseHandlers(self.client)

        # Log initialization based on environment
        if LOG_LEVEL == logging.DEBUG:
            logger.debug("LLM Orchestrator initialized in DEBUG mode")
        else:
            logger.info("LLM Orchestrator initialized in production mode")

    async def _generate_recovery_response(
        self, user_message: str, session_id: str, model: str, error: Exception
    ) -> Dict[str, Any]:
        """Always restart on errors - no complex recovery options."""

        # Always clear session on any error
        self.conversation_states[session_id] = ConversationState()

        restart_message = """I encountered an issue and have reset our conversation.

Let's start fresh! Please provide your beam requirements:
- Material: Steel, Wood, or Concrete
- Length: in mm or meters  
- Load: in N or kN
- Height: in mm (required)
- Width: in mm (required)

Example: "Steel beam, 6000mm long, 20000N load, 200mm height, 100mm width" """

        return {
            "action": "error_restart",
            "llm_response": restart_message,
            "require_user_input": True,
            "beam_spec": {},
            "phase": "gathering_info",
            "error_logged": True,
        }

    async def process_user_input(
        self,
        user_message: str,
        model: str,
        session_id: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Strict linear state machine - no jumping between phases.

        Args:
            user_message: User's input text
            model: Claude model to use (claude-3-5-sonnet-20241022 or claude-3-5-haiku-20241022)
            session_id: Unique session identifier
            json_data: Optional JSON data from uploaded file

        Returns:
            Structured response dictionary
        """
        json_info = (
            f" with JSON data: {json.dumps(json_data, indent=2)[:100]}{'...' if json_data and len(str(json_data)) > 100 else ''}"
            if json_data
            else ""
        )
        logger.debug(
            f"[SESSION {session_id}] Processing input: '{user_message[:100]}{'...' if len(user_message) > 100 else ''}' using model: {model}{json_info}"
        )

        try:
            # Get or create session
            if session_id not in self.conversation_states:
                self.conversation_states[session_id] = ConversationState()
            state = self.conversation_states[session_id]

            logger.debug(f"[SESSION {session_id}] Current phase: {state.phase.value}")
            logger.debug(
                f"[SESSION {session_id}] Current beam spec: {json.dumps(state.beam_spec, indent=2)}"
            )
            logger.debug(
                f"[SESSION {session_id}] Missing fields: {state.missing_fields}"
            )

            # Check for reset intent first (from any phase)
            if await self.intent_detector.detect_reset_intent(user_message, model):
                logger.info(
                    f"[SESSION {session_id}] Reset intent detected - clearing all session data"
                )
                self.conversation_states[session_id] = ConversationState()
                state = self.conversation_states[session_id]
                return {
                    "action": "session_reset",
                    "llm_response": "Starting fresh! Please tell me about your new beam requirements.",
                    "require_user_input": True,
                    "beam_spec": {},
                    "phase": state.phase.value,
                }

            # Strict linear progression
            if state.phase == ConversationPhase.GATHERING:
                return await self.phase_handlers.handle_gathering_phase(
                    user_message, state, model, json_data
                )

            elif state.phase == ConversationPhase.ANALYZING:
                if await self.intent_detector.detect_history_request(
                    user_message, model
                ):
                    state.transition_to(ConversationPhase.HISTORY_RESULTS)
                    return await self.phase_handlers.handle_history_results(
                        state, model
                    )
                else:
                    return await self.phase_handlers.handle_analyzing_only(state, model)

            elif state.phase == ConversationPhase.HISTORY_RESULTS:
                if await self.intent_detector.detect_optimization_request(
                    user_message, model
                ):
                    state.transition_to(ConversationPhase.OPTIMIZING)
                    return await self.phase_handlers.handle_optimization(state, model)
                else:
                    return await self.phase_handlers.handle_history_results(
                        state, model
                    )

            elif state.phase == ConversationPhase.OPTIMIZING:
                response = await self.phase_handlers.handle_optimization(state, model)
                state.transition_to(ConversationPhase.COMPLETED)
                return response

            elif state.phase == ConversationPhase.COMPLETED:
                # Only allow new beam design from completed state
                state.transition_to(ConversationPhase.GATHERING)
                return await self.phase_handlers.handle_gathering_phase(
                    user_message, state, model, json_data
                )

        except Exception as e:
            logger.error(f"Error in session {session_id}: {str(e)}")
            return await self._generate_recovery_response(
                user_message, session_id, model, e
            )

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state."""
        if session_id in self.conversation_states:
            return self.conversation_states[session_id].to_dict()
        return None

    def clear_session(self, session_id: str):
        """Clear session state."""
        if session_id in self.conversation_states:
            del self.conversation_states[session_id]
