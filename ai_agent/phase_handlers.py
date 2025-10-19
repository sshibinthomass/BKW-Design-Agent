"""
Conversation phase handling methods for the LLM Orchestrator system.
"""

import asyncio
import json
import logging
from typing import Dict, Any
from anthropic import Anthropic

from .enums import get_system_prompt, ConversationPhase
from .conversation_state import ConversationState
from .beam_processor import BeamProcessor
from .intent_detector import IntentDetector
from .historical_analyzer import HistoricalAnalyzer
from .visualization_handler import VisualizationHandler
from ai_agent.model_status_predict.script import (
    inference_mode,
    optimize_mode_for_webapp,
)

logger = logging.getLogger(__name__)


class PhaseHandlers:
    """Handles different conversation phases in the beam design workflow."""

    def __init__(self, anthropic_client: Anthropic):
        self.client = anthropic_client
        self.beam_processor = BeamProcessor(anthropic_client)
        self.intent_detector = IntentDetector(anthropic_client)
        self.historical_analyzer = HistoricalAnalyzer()
        self.visualization_handler = VisualizationHandler()

    async def _get_llm_response(
        self, model: str, system_prompt: str, context: str
    ) -> str:
        """Helper method to get LLM response with error handling."""
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=model,
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": context}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return "I'm having trouble processing your request. Could you please try rephrasing?"

    async def handle_gathering_phase(
        self,
        user_message: str,
        state: ConversationState,
        model: str,
        json_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Handle the gathering phase - collect beam specifications."""
        # Extract info from message and/or JSON
        extracted_info = await self.beam_processor.extract_beam_info(
            user_message, model, json_data
        )
        if extracted_info:
            logger.debug(f"Updating beam spec with: {extracted_info}")
            state.update_beam_spec(extracted_info)

        if state.is_complete_for_analysis():
            # Transition to analyzing phase
            state.transition_to(ConversationPhase.ANALYZING)
            return await self.handle_analyzing_only(state, model)
        else:
            # Still need more info
            return await self.gather_missing_info(user_message, state, model)

    async def handle_analyzing_only(
        self, state: ConversationState, model: str
    ) -> Dict[str, Any]:
        """Handle ANALYZING phase - show current beam analysis and ask for history."""

        # Generate visualization with "Current Beam Design" title
        visualization_json = (
            self.visualization_handler.generate_visualization_with_title(
                state.beam_spec, "Current Beam Design"
            )
        )

        # Get current beam status
        visualizer_spec = self.beam_processor.convert_spec_for_visualizer(
            state.beam_spec
        )
        status_data = inference_mode(visualizer_spec)

        # Get system prompt for analysis only
        system_prompt = get_system_prompt("analyze_only")

        # Create context for current beam analysis
        context = f"""
Current Beam Analysis:
{status_data}

Your task: Present the current beam analysis results and ask if user wants to see historical alternatives for comparison. Use attractive formatting (e.g., **bold**). Be clear, concise, and professional.
"""

        # Generate LLM response
        llm_response = await self._get_llm_response(model, system_prompt, context)

        return {
            "action": "analyze_only",
            "llm_response": llm_response,
            "beam_spec": state.beam_spec,
            "beam_status": status_data,
            "visualization": visualization_json,
            "require_user_input": True,
            "next_actions": ["show_history", "new_beam"],
        }

    async def handle_history_results(
        self, state: ConversationState, model: str
    ) -> Dict[str, Any]:
        """Handle HISTORY_RESULTS phase - show historical comparison and ask for optimization."""

        # Find best historical alternative
        best_historical = self.historical_analyzer.find_best_historical_design(
            state.beam_spec
        )

        # Generate visualization with "Best Historical Data" title
        if best_historical:
            # Create beam spec for historical design
            historical_spec = {
                "material": state.beam_spec["material"],
                "length_mm": state.beam_spec["length_mm"],
                "load_n": state.beam_spec["load_n"],
                "width_mm": best_historical["width_mm"],
                "height_mm": best_historical["height_mm"],
            }
            visualization_json = (
                self.visualization_handler.generate_visualization_with_title(
                    historical_spec, "Best Historical Data"
                )
            )
        else:
            # No historical data, show current design
            visualization_json = (
                self.visualization_handler.generate_visualization_with_title(
                    state.beam_spec, "Best Historical Data"
                )
            )
        logger.info(f"Historical status 1: {best_historical}")
        # Get system prompt for history results with status information
        system_prompt = get_system_prompt(
            "show_history",
            historical_status=best_historical.get("status", "PASS")
            if best_historical
            else "PASS",
        )

        # Create context with historical comparison
        context = f"""
Historical Database Analysis:
{self.historical_analyzer.format_historical_context(best_historical, state.beam_spec)}

Your task: Present historical comparison results, specify the Material, Height, Width, and Length of the historical alternative if available, compare with current design and put emphasis on the potential volume reduction if available, then ask if user wants optimization. Use attractive formatting (e.g., **bold**). Be clear, concise, and professional. also mention the deflection and allowable deflection of the historical alternative if available.
"""

        # Generate LLM response
        llm_response = await self._get_llm_response(model, system_prompt, context)

        return {
            "action": "show_history",
            "llm_response": llm_response,
            "beam_spec": state.beam_spec,
            "best_historical": best_historical,
            "visualization": visualization_json,
            "require_user_input": True,
            "next_actions": ["optimize_design", "new_beam"],
        }

    async def gather_missing_info(
        self, user_message: str, state: ConversationState, model: str
    ) -> Dict[str, Any]:
        """Behavior 1: Gather missing beam information through conversation."""

        system_prompt = get_system_prompt("gather_info", state=state.to_dict())

        # Create context about what we know and what we need
        context = f"""
You are assisting a user in specifying a structural beam.

Current beam specifications (extracted so far):
{json.dumps(state.beam_spec, indent=2)}

Missing required fields: {state.missing_fields}

User's latest message:
"{user_message}"

Your task:
- Reply in the same language as the user's message (English or German only).
- Respond conversationally to help gather the missing information.
- Ask specific, helpful questions about the missing fields.
- If helpful, include example units (e.g., "in mm", "in kN").
- Be brief, clear, and polite.
- Do NOT confirm or validate current values — focus only on what's missing.
"""

        try:
            llm_response = await self._get_llm_response(model, system_prompt, context)

            return {
                "action": "gather_info",
                "llm_response": llm_response,
                "beam_spec": state.beam_spec,
                "missing_fields": state.missing_fields,
                "require_user_input": True,
                "next_actions": ["provide_missing_info"],
            }

        except Exception as e:
            logger.error(f"Error in gather_missing_info: {e}")
            return {
                "action": "error",
                "llm_response": "I'm having trouble processing your request. Could you please try rephrasing?",
                "require_user_input": True,
            }

    async def handle_complete_spec(
        self, state: ConversationState, model: str
    ) -> Dict[str, Any]:
        """Handle complete beam specification with LLM response and visualization."""

        # Generate visualization
        visualization_json = (
            self.visualization_handler.generate_visualization_with_title(
                state.beam_spec, "Current Beam Design"
            )
        )

        # Get current beam status
        visualizer_spec = self.beam_processor.convert_spec_for_visualizer(
            state.beam_spec
        )
        status_data = inference_mode(visualizer_spec)

        # Find best historical alternative
        best_historical = self.historical_analyzer.find_best_historical_design(
            state.beam_spec
        )

        # Get system prompt for complete spec handling with status information
        system_prompt = get_system_prompt(
            "complete_spec",
            historical_status=best_historical.get("status", "PASS")
            if best_historical
            else "PASS",
            state=state.to_dict(),
        )
        logger.info(f"Historical status 2: {best_historical}")

        # Create enhanced context with historical comparison
        context = f"""
Current Beam Analysis:
{status_data}

Historical Database Analysis:
{self.historical_analyzer.format_historical_context(best_historical, state.beam_spec)}

Your task: Present analysis results, compare with historical alternative if available, specify the Material, Height, Width, and Length of the historical alternative if available, compare with historical alternative and put emphasis on the potential volume reduction if available and ask if user wants optimization. Use attractive formatting (e.g., **bold**). Be clear, concise, and professional.
"""

        # Generate LLM response
        llm_response = await self._get_llm_response(model, system_prompt, context)

        return {
            "action": "analyze_beam",
            "llm_response": llm_response,
            "beam_spec": state.beam_spec,
            "beam_status": status_data,
            "best_historical": best_historical,
            "visualization": visualization_json,
            "require_user_input": True,
            "next_actions": ["optimize_design", "modify_spec", "new_beam"],
        }

    async def handle_optimization(
        self, state: ConversationState, model: str
    ) -> Dict[str, Any]:
        """Handle beam optimization request using the streamlined optimization function."""

        try:
            # Call the optimization function from streamlined script
            logger.info(f"Running optimization for beam: {state.beam_spec}")

            optimization_result = optimize_mode_for_webapp(
                length=state.beam_spec["length_mm"],
                material=state.beam_spec["material"],
                force=state.beam_spec["load_n"],
                user_height=state.beam_spec.get("height_mm"),
                user_width=state.beam_spec["width_mm"],
            )

            logger.info(f"Optimization result: {optimization_result}")

            if optimization_result["success"]:
                # Generate visualization for optimized beam with "Optimized Model" title
                optimized_spec = {
                    "material": state.beam_spec["material"],
                    "length_mm": state.beam_spec["length_mm"],
                    "load_n": state.beam_spec["load_n"],
                    "width_mm": optimization_result["width"],
                    "height_mm": optimization_result["height"],
                }
                visualization_json = (
                    self.visualization_handler.generate_visualization_with_title(
                        optimized_spec, "Optimized Model"
                    )
                )

                # Get system prompt for optimization results
                system_prompt = get_system_prompt("optimize_design")

                # Prepare optimization context based on optimization category
                optimization_category = optimization_result.get(
                    "optimization_category", "unknown"
                )

                if optimization_category == "optimization_success":
                    context = f"""
Optimization Success - Material Reduction Achieved:

Original Design:
- Dimensions: {state.beam_spec["width_mm"]}×{state.beam_spec["height_mm"]} mm
- Volume: {optimization_result["original_volume"]:,.0f} mm³
- Status: Structurally Safe

Optimized Design:
- Dimensions: {optimization_result["width"]:.1f}×{optimization_result["height"]:.1f} mm  
- Volume: {optimization_result["volume"]:,.0f} mm³
- Deflection: {optimization_result["deflection"]:.2f} mm (within {optimization_result["allowable_deflection"]:.2f} mm limit)

Volume Reduction: {abs(optimization_result["volume_change_percent"]):.1f}%
Status: SUCCESSFUL OPTIMIZATION

Your task: Present the successful optimization with volume reduction and ask if user wants to restart the process.
"""
                elif optimization_category == "safety_upgrade":
                    base_context = f"""
Structural Safety Analysis - Design Upgrade Required:

Original Design (UNSAFE):
- Dimensions: {state.beam_spec["width_mm"]}×{state.beam_spec["height_mm"]} mm
- Volume: {optimization_result["original_volume"]:,.0f} mm³
- Deflection: {optimization_result["original_deflection"]:.2f} mm (exceeds {optimization_result["allowable_deflection"]:.2f} mm limit)
- Status: FAILS STRUCTURAL SAFETY

Minimum Safe Custom Design:
- Dimensions: {optimization_result["width"]:.1f}×{optimization_result["height"]:.1f} mm
- Volume: {optimization_result["volume"]:,.0f} mm³  
- Deflection: {optimization_result["deflection"]:.2f} mm (within safety limits)
- Material Increase: {optimization_result["volume_change_percent"]:.1f}% (Required for Safety)
"""

                    if optimization_result.get("has_better_standard"):
                        std_beam = optimization_result["standard_beam_alternative"]
                        context = (
                            base_context
                            + f"""
RECOMMENDED STANDARD BEAM ALTERNATIVE:
- Profile: {std_beam["profile"]} 
- Dimensions: {std_beam["width"]:.1f}×{std_beam["height"]:.1f} mm
- Volume: {std_beam["volume"]:,.0f} mm³
- Deflection: {std_beam["deflection"]:.2f} mm (safe)
- Efficiency: {std_beam["efficiency_gain"]:.1f}% MORE EFFICIENT than custom design

Your task: Explain the original design was unsafe and present both the minimum custom solution and the more efficient standard beam recommendation. Emphasize the standard beam as the better choice.
"""
                        )
                    else:
                        context = (
                            base_context
                            + """
Your task: Explain that the original design was structurally inadequate and the larger beam is necessary for safety. This is the minimum safe design, not an optimization failure.
"""
                        )

                elif optimization_category == "design_feasible":
                    context = f"""
Design Analysis - Original Design Adequate:

Original Design:
- Dimensions: {state.beam_spec["width_mm"]}×{state.beam_spec["height_mm"]} mm
- Volume: {optimization_result["original_volume"]:,.0f} mm³
- Status: Structurally Safe and Adequate

Alternative Design Explored:
- Dimensions: {optimization_result["width"]:.1f}×{optimization_result["height"]:.1f} mm
- Volume: {optimization_result["volume"]:,.0f} mm³
- Material Change: {optimization_result["volume_change_percent"]:.1f}%

Your task: Confirm the original design is adequate and explain that the alternative uses more material without significant benefit.
"""
                else:  # minimum_feasible or unknown
                    context = f"""
Optimization Results:

Minimum Feasible Design:
- Dimensions: {optimization_result["width"]:.1f}×{optimization_result["height"]:.1f} mm
- Volume: {optimization_result["volume"]:,.0f} mm³
- Deflection: {optimization_result["deflection"]:.2f} mm (within {optimization_result["allowable_deflection"]:.2f} mm limit)
- Assessment: {optimization_result["assessment"]}

Your task: Present the minimum feasible design and ask if user wants to accept it and restart the process.
"""

                # Generate LLM response
                llm_response = await self._get_llm_response(
                    model, system_prompt, context
                )

                return {
                    "action": "optimize_design",
                    "llm_response": llm_response,
                    "beam_spec": state.beam_spec,
                    "optimization_result": {
                        "success": True,
                        "optimal_height": optimization_result["height"],
                        "optimal_width": optimization_result["width"],
                        "optimal_volume": optimization_result["volume"],
                        "optimal_deflection": optimization_result["deflection"],
                        "volume_savings": optimization_result.get(
                            "volume_change_percent", 0
                        ),
                        "allowable_deflection": optimization_result[
                            "allowable_deflection"
                        ],
                    },
                    "visualization": visualization_json,
                    "require_user_input": True,
                    "next_actions": ["accept_optimization", "modify_spec", "new_beam"],
                }
            else:
                # Optimization failed
                logger.warning(
                    f"Optimization failed: {optimization_result.get('error', 'Unknown error')}"
                )

                system_prompt = get_system_prompt("optimize_design")
                context = f"""
Optimization Failed:

The optimization process could not find a better design for your beam specifications.
Error: {optimization_result.get("error", "No feasible solution found")}

This might happen if:
- The current design is already very efficient
- The constraints are too restrictive
- The load requirements are very demanding

Your task: Explain the optimization failure politely and suggest to restart the beam selection process.
"""

                llm_response = await self._get_llm_response(
                    model, system_prompt, context
                )

                return {
                    "action": "optimize_design",
                    "llm_response": llm_response,
                    "beam_spec": state.beam_spec,
                    "optimization_result": {
                        "success": False,
                        "error": optimization_result.get(
                            "error", "Optimization failed"
                        ),
                    },
                    "require_user_input": True,
                    "next_actions": ["modify_spec", "new_beam"],
                }

        except Exception as e:
            logger.error(f"Error in optimization handling: {e}")
            return {
                "action": "error",
                "llm_response": "I encountered an error while optimizing your beam design. Please try again or modify your specifications.",
                "require_user_input": True,
            }
