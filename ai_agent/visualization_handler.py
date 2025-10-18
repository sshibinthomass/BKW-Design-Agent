"""
Beam visualization generation utilities.
"""

import logging
import sys
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class VisualizationHandler:
    """Handles beam visualization generation."""

    def __init__(self):
        # Add parent directory to path for beam_visualizer import
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    def generate_visualization_with_title(
        self, beam_spec: Dict[str, Any], title: str
    ) -> Optional[str]:
        """Generate beam visualization with custom title."""
        try:
            from beam_visualizer import visualize_beam_from_data

            # Convert spec to visualizer format
            visualizer_spec = self._convert_spec_for_visualizer(beam_spec)
            logger.info(
                f"Generating visualization '{title}' for spec: {visualizer_spec}"
            )

            # Generate visualization
            fig = visualize_beam_from_data(visualizer_spec)

            # Update the title by prefixing to original title
            original_title = (
                fig.layout.title.text
                if fig.layout.title and fig.layout.title.text
                else "Beam Visualization"
            )
            new_title = f"{title}: {original_title}"
            fig.update_layout(title=new_title)

            # Convert to JSON
            visualization_json = fig.to_json()
            logger.info(f"[SUCCESS] Visualization '{title}' generated successfully")
            return visualization_json

        except Exception as e:
            logger.warning(f"[WARNING] Visualization '{title}' generation failed: {e}")
            return None

    def _convert_spec_for_visualizer(self, beam_spec: Dict[str, Any]) -> Dict[str, str]:
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
