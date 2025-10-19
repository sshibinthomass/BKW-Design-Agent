"""
Historical data analysis and comparison utilities.
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HistoricalAnalyzer:
    """Handles historical beam data analysis and comparison."""

    def __init__(self, historical_data_path: str = "extracted_historical_data_00.csv"):
        self.historical_data_path = historical_data_path
        self.historical_data = None
        self._load_historical_data()

    def _load_historical_data(self):
        """Load historical data from CSV file."""
        try:
            if os.path.exists(self.historical_data_path):
                self.historical_data = pd.read_csv(
                    self.historical_data_path, delimiter=";"
                )
                logger.info(
                    f"Loaded {len(self.historical_data)} historical beam designs"
                )
            else:
                logger.warning(
                    f"Historical data file not found: {self.historical_data_path}"
                )
                self.historical_data = None
        except Exception as e:
            logger.warning(f"Could not load historical data: {e}")
            self.historical_data = None

    def _reload_historical_data(self):
        """Reload historical data from CSV file to get latest entries"""
        try:
            if os.path.exists(self.historical_data_path):
                self.historical_data = pd.read_csv(
                    self.historical_data_path, delimiter=";"
                )
                logger.debug(
                    f"Reloaded {len(self.historical_data)} historical beam designs"
                )
                return True
            else:
                logger.warning(
                    f"Historical data file not found: {self.historical_data_path}"
                )
                self.historical_data = None
                return False
        except Exception as e:
            logger.warning(f"Could not reload historical data: {e}")
            self.historical_data = None
            return False

    def find_best_historical_design(
        self, beam_spec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find single best PASSING design with minimum volume for same material+length"""
        # Reload historical data to get latest entries
        self._reload_historical_data()

        if self.historical_data is None:
            return None

        try:
            # Filter by exact material and length (±5% tolerance)
            logger.info(f"Filtering historical data for beam spec: {beam_spec}")
            material = beam_spec["material"]
            length = beam_spec["length_mm"]
            length_tolerance = length * 0.05  # 5% tolerance
            logger.info(f"Length tolerance: {length_tolerance}")
            logger.info(f"Length: {length}")
            logger.info(f"Material: {material}")
            logger.info(f"Historical data: {self.historical_data}")
            logger.info(f"Status: {self.historical_data['Status']}")
            logger.info(f"L (mm): {self.historical_data['L (mm)']}")
            logger.info(f"V (mm^3): {self.historical_data['V (mm^3)']}")
            logger.info(f"Status: {self.historical_data['Status']}")
            logger.info(f"L (mm): {self.historical_data['L (mm)']}")
            logger.info(f"V (mm^3): {self.historical_data['V (mm^3)']}")
            logger.info(
                f"Allowable Deflection: {self.historical_data['Allowable_Def (mm) L/240']}"
            )
            filtered = self.historical_data[
                (self.historical_data["Material"] == material)
                & (self.historical_data["L (mm)"] >= length - length_tolerance)
                & (self.historical_data["L (mm)"] <= length + length_tolerance)
                & (self.historical_data["Status"].isin(["PASS", "OPT"]))
            ]

            if filtered.empty:
                return None

            # Return design with minimum volume
            best_design = filtered.loc[filtered["V (mm^3)"].idxmin()]

            # Calculate current volume (handle missing height_mm)
            current_height = beam_spec.get(
                "height_mm", 100
            )  # Default 100mm if not provided
            current_volume = (
                beam_spec["length_mm"] * current_height * beam_spec["width_mm"]
            )
            historical_volume = float(
                best_design["V (mm^3)"]
            )  # Convert to Python float
            efficiency_improvement = (
                (current_volume - historical_volume) / current_volume
            ) * 100

            return {
                "height_mm": float(
                    best_design["h (mm)"]
                ),  # Convert numpy to Python float
                "width_mm": float(best_design["w (mm)"]),
                "volume_mm3": historical_volume,
                "deflection_mm": float(best_design["Deflection (mm)"]),
                "efficiency_improvement": efficiency_improvement,
                "status": str(best_design["Status"]),  # Include actual status from CSV
                "allowable_deflection_mm": float(
                    best_design["Allowable_Def (mm) L/240"]
                ),
            }

        except Exception as e:
            logger.error(f"Error finding best historical design: {e}")
            return None

    def format_historical_context(
        self, best_historical: Optional[Dict[str, Any]], current_spec: Dict[str, Any]
    ) -> str:
        """Format historical data for LLM context"""
        if best_historical is None:
            return (
                "No historical data available for this material and length combination."
            )

        # Handle missing height_mm
        current_height = current_spec.get(
            "height_mm", 100
        )  # Default 100mm if not provided
        current_volume = (
            current_spec["length_mm"] * current_height * current_spec["width_mm"]
        )
        logger.info(f"best historical: {best_historical}")
        return f"""
Best Historical Design Found:
- Material: {current_spec["material"]} (same)
- Length: {current_spec["length_mm"]} mm (same)
- Dimensions: {best_historical["height_mm"]:.0f}×{best_historical["width_mm"]:.0f} mm
- Volume: {best_historical["volume_mm3"]:,.0f} mm³
- Deflection: {best_historical["deflection_mm"]:.1f} mm
- Allowable Deflection: {best_historical["allowable_deflection_mm"]:.1f} mm
- Status: {best_historical.get("status", "PASS")}

Comparison with Current Design:
- Current Volume: {current_volume:,.0f} mm³
- Historical Volume: {best_historical["volume_mm3"]:,.0f} mm³
- Potential Savings: {best_historical["efficiency_improvement"]:+.1f}%
"""
