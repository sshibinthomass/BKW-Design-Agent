"""
Intent detection utilities for the LLM Orchestrator system.
"""

import asyncio
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class IntentDetector:
    """Handles LLM-based intent detection for user messages."""

    def __init__(self, anthropic_client: Anthropic):
        self.client = anthropic_client

    async def detect_reset_intent(self, user_message: str, model: str) -> bool:
        """Detect if user wants to start completely fresh using LLM."""

        detection_prompt = f"""
You are an intent detector for GenDesign beam analysis.

The user is in an active beam design session and may want to start completely fresh with a new beam.
Determine if they want to reset/restart the entire session and begin with a new beam design.

Return ONLY "true" or "false" (lowercase, no quotes).

Reset/Restart indicators (English/German/Other languages):
✓ new beam/neuer träger, fresh start/neuer anfang, start over/von vorne
✓ different beam/anderer träger, another beam/noch ein träger
✓ restart/neustart, reset/zurücksetzen, begin again/wieder anfangen
✓ clear/löschen, fresh design/neues design, different design/anderes design
✓ "I want to design a new beam", "Let's start fresh", "Can we restart?"

Non-reset responses:
✗ questions about current analysis, modification requests
✗ optimization requests, historical data requests
✗ clarification questions, help requests
✗ continuing with current beam discussion

Examples:
"I want to design a new beam" → true
"Ich möchte einen neuen Träger entwerfen" → true
"Let's start fresh" → true
"Can we restart?" → true
"Von vorne anfangen" → true
"What does PASS mean?" → false
"Optimize this beam" → false
"Change the width to 150mm" → false

User message: "{user_message}"
"""

        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": detection_prompt}],
            )

            result = response.content[0].text.strip().lower()
            is_reset_request = result == "true"

            logger.info(f"[RESET DETECTION] '{user_message}' -> {is_reset_request}")
            return is_reset_request

        except Exception as e:
            logger.error(f"Reset detection failed: {e}")
            # Fallback to pattern matching for robustness
            logger.warning("Falling back to pattern-matching for reset detection")
            reset_patterns = [
                "new beam",
                "start over",
                "fresh design",
                "different beam",
                "another beam",
                "restart",
                "neuer träger",
                "von vorne",
                "neu anfangen",
                "anderer träger",
                "neues design",
                "neustart",
            ]
            return any(pattern in user_message.lower() for pattern in reset_patterns)

    async def detect_history_request(self, user_message: str, model: str) -> bool:
        """Detect if user wants to see historical data comparison."""

        detection_prompt = f"""
You are an intent detector for GenDesign beam analysis.

The user has seen the current beam analysis results.
Now determine if they want to see historical alternatives for comparison.

Return ONLY "true" or "false" (lowercase, no quotes).

History indicators (English/German):
✓ yes/ja, show/zeigen, history/geschichte, historical/historisch
✓ alternatives/alternativen, comparison/vergleich, compare/vergleichen
✓ see/sehen, show me/zeig mir, view/ansehen
✓ "show historical", "see alternatives", "compare with history"

Non-history responses:
✗ no/nein, maybe/vielleicht, not now/nicht jetzt
✗ questions about current analysis
✗ modification requests (change material, dimensions)
✗ optimization requests, new beam requests

Examples:
"Yes, show me historical data" → true
"Ja, zeig mir Alternativen" → true
"Can I see alternatives?" → true
"No, thanks" → false
"What does PASS mean?" → false
"Optimize this beam" → false

User message: "{user_message}"
"""

        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": detection_prompt}],
            )

            result = response.content[0].text.strip().lower()
            is_history_request = result == "true"

            logger.info(f"[HISTORY DETECTION] '{user_message}' -> {is_history_request}")
            return is_history_request

        except Exception as e:
            logger.error(f"History detection failed: {e}")
            return False

    async def detect_optimization_request(self, user_message: str, model: str) -> bool:
        """Detect if user wants optimization. Only called when beam specs are complete."""

        detection_prompt = f"""
You are an intent detector for GenDesign beam optimization.

The user has already provided complete beam specifications and seen the analysis results.
Now determine if they want to optimize the beam design.

Return ONLY "true" or "false" (lowercase, no quotes).

Optimization indicators (English/German):
✓ yes/ja, optimize/optimieren, improve/verbessern, better/besser
✓ find optimal/optimale finden, make efficient/effizienter machen
✓ reduce volume/volumen reduzieren, minimize/minimieren
✓ "run optimization", "start optimization"

Non-optimization responses:
✗ no/nein, maybe/vielleicht, not now/nicht jetzt
✗ questions about analysis, requests for explanation
✗ modification requests (change material, dimensions)
✗ new beam requests

Examples:
"Yes, optimize this design" → true
"Ja, optimiere das Design" → true
"Can you optimize it?" → true
"No, thanks" → false
"What does PASS mean?" → false
"Change material to wood" → false

User message: "{user_message}"
"""

        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": detection_prompt}],
            )

            result = response.content[0].text.strip().lower()
            is_optimization = result == "true"

            logger.info(
                f"[OPTIMIZATION DETECTION] '{user_message}' -> {is_optimization}"
            )
            return is_optimization

        except Exception as e:
            logger.error(f"Optimization detection failed: {e}")
            return False
