"""
Beam data extraction and processing utilities.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class BeamProcessor:
    """Handles beam data extraction and processing from user input and JSON files."""

    def __init__(self, anthropic_client: Anthropic):
        self.client = anthropic_client

    async def extract_beam_info(
        self, user_message: str, model: str, json_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract beam specifications from user message and/or JSON data using LLM with strict JSON output."""

        # If JSON data is provided, extract beam specs directly and include in context
        json_context = ""
        extracted_from_json = {}

        if json_data:
            logger.info(f"Processing JSON file data: {json_data}")
            # Extract beam specifications from JSON data
            extracted_from_json = self._parse_json_beam_data(json_data)
            logger.info(f"Extracted from JSON: {extracted_from_json}")

            json_context = f"""

JSON FILE ATTACHED:
The user has attached a JSON file with the following beam data:
{json.dumps(json_data, indent=2)}

From this JSON file, I extracted: {json.dumps(extracted_from_json, indent=2)}
"""

        extraction_prompt = f"""You are a JSON Data Extractor for GenDesign, assisting users in selecting and analyzing beams.  
Inputs may be in English or German. Extract beam specifications and return ONLY valid JSON with these fields:  
"material", "length_mm", "load_n", "height_mm", "width_mm".

Valid materials in English or German are:  
- Steel / Stahl  
- Wood / Holz  
- Concrete / Beton

Units may use meters (m) or millimeters (mm), loads may be in kN or N.  
Convert all units to millimeters (mm) and Newtons (N) accordingly.

Partial data allowed. Return {{}} only if no valid fields are found.

EXAMPLES:  
Input (English): "steel beam 6m long 20kN"  
Output: {{"material": "Steel", "length_mm": 6000, "load_n": 20000}}

Input (German): "Stahlträger 6m lang 20kN"  
Output: {{"material": "Steel", "length_mm": 6000, "load_n": 20000}}

Input (German): "Beton, 5000mm Höhe 200mm"  
Output: {{"material": "Concrete", "length_mm": 5000, "height_mm": 200}}

Input (English): "I need a steel beam"  
Output: {{"material": "Steel"}}

Input (German): "Ich brauche einen 50m langen Träger"  
Output: {{"length_mm": 50000}}

Input (German): "Hallo, wie geht's?"  
Output: {{}}

{json_context}

NOW EXTRACT FROM USER MESSAGE: """
        extraction_prompt += f'"{user_message}"'

        # If we have JSON data but no user message, return the JSON extracted data directly
        if json_data and not user_message.strip():
            return extracted_from_json if extracted_from_json else {}

        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=model,
                max_tokens=150,
                messages=[{"role": "user", "content": extraction_prompt}],
            )

            content = response.content[0].text.strip()
            logger.debug(f"Raw LLM extraction response: {repr(content)}")

            # Clean up response
            content = content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            # Validate JSON
            if content.startswith("{") and content.endswith("}"):
                extracted_info = json.loads(content)

                # Combine JSON extracted data with text extracted data
                combined_info = {
                    **extracted_from_json,
                    **extracted_info,
                }  # Text data overrides JSON data

                logger.info(f"[SUCCESS] LLM successfully extracted: {extracted_info}")
                if extracted_from_json:
                    logger.info(f"[SUCCESS] Combined with JSON data: {combined_info}")

                return combined_info if combined_info else {}
            elif content == "{}":
                logger.info("[INFO] LLM found no beam information in input")
                # Return JSON data if available, even if no text info was found
                return extracted_from_json if extracted_from_json else {}
            else:
                logger.warning(
                    f"[WARNING] Invalid JSON format from LLM: {repr(content)}"
                )
                # Return JSON data if available, even if text processing failed
                return extracted_from_json if extracted_from_json else {}

        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] JSON parsing failed: {e}, content: {repr(content)}")
            return {}
        except Exception as e:
            logger.error(f"[ERROR] LLM extraction failed: {e}")
            return {}

    def _parse_json_beam_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse beam specifications from uploaded JSON file."""
        extracted = {}

        try:
            # Handle common JSON field mappings
            field_mappings = {
                "Material": "material",
                "material": "material",
                "Length": "length_mm",
                "length": "length_mm",
                "Load": "load_n",
                "load": "load_n",
                "Height": "height_mm",
                "height": "height_mm",
                "Width": "width_mm",
                "width": "width_mm",
            }

            for json_key, beam_key in field_mappings.items():
                if json_key in json_data:
                    value = json_data[json_key]

                    # Handle material
                    if beam_key == "material":
                        if isinstance(value, str):
                            extracted[beam_key] = value.strip().capitalize()

                    # Handle numeric values with units
                    elif beam_key in ["length_mm", "height_mm", "width_mm"]:
                        if isinstance(value, str):
                            # Extract numeric value from string like "5000 mm" or "5 m"
                            match = re.search(r"([0-9.]+)\s*(mm|m)?", value.lower())
                            if match:
                                num_value = float(match.group(1))
                                unit = match.group(2) if match.group(2) else "mm"
                                if unit == "m":
                                    num_value *= 1000  # Convert to mm
                                extracted[beam_key] = int(num_value)
                        elif isinstance(value, (int, float)):
                            extracted[beam_key] = int(value)

                    # Handle load with units
                    elif beam_key == "load_n":
                        if isinstance(value, str):
                            # Extract numeric value from string like "10000 N" or "10 kN"
                            match = re.search(r"([0-9.]+)\s*(n|kn)?", value.lower())
                            if match:
                                num_value = float(match.group(1))
                                unit = match.group(2) if match.group(2) else "n"
                                if unit == "kn":
                                    num_value *= 1000  # Convert to N
                                extracted[beam_key] = int(num_value)
                        elif isinstance(value, (int, float)):
                            extracted[beam_key] = int(value)

            logger.info(f"Successfully parsed JSON beam data: {extracted}")
            return extracted

        except Exception as e:
            logger.error(f"Error parsing JSON beam data: {e}")
            return {}

    def convert_spec_for_visualizer(self, beam_spec: Dict[str, Any]) -> Dict[str, str]:
        """Convert beam spec from numeric format to visualizer string format."""
        converted = {}

        # Material mapping (capitalize first letter)
        if "material" in beam_spec:
            converted["Material"] = beam_spec["material"]

        # Length conversion
        if "length_mm" in beam_spec:
            converted["Length"] = f"{beam_spec['length_mm']} mm"

        # Load conversion
        if "load_n" in beam_spec:
            converted["Load"] = f"{beam_spec['load_n']} N"

        # Dimensions conversion
        if "width_mm" in beam_spec:
            converted["Width"] = f"{beam_spec['width_mm']} mm"
        if "height_mm" in beam_spec:
            converted["Height"] = f"{beam_spec['height_mm']} mm"

        logger.debug(f"Converted beam spec: {beam_spec} -> {converted}")
        return converted
