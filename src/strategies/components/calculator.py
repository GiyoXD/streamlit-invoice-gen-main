# Calculator Component
# Handles CBM, pallet count calculations and truck/container selection

from typing import Dict, Any, Tuple, Optional
import math


class Calculator:
    """Component for calculating CBM, pallet counts and recommending trucks/containers"""

    # Truck and container specifications
    TRUCK_CAPACITIES = {
        '3ton': {
            'max_weight_kg': 3000,
            'max_cbm': 15,
            'max_pallets': 6,
            'description': '3-ton truck for small loads'
        },
        '5ton': {
            'max_weight_kg': 5000,
            'max_cbm': 25,
            'max_pallets': 10,
            'description': '5-ton truck for medium loads'
        },
        '8ton': {
            'max_weight_kg': 8000,
            'max_cbm': 40,
            'max_pallets': 16,
            'description': '8-ton truck for larger loads'
        },
        '20gp': {
            'max_weight_kg': 28000,
            'max_cbm': 33.2,  # Standard 20ft container
            'max_pallets': 20,
            'description': '20ft General Purpose container'
        },
        '40hc': {
            'max_weight_kg': 28000,
            'max_cbm': 76.4,  # Standard 40ft High Cube
            'max_pallets': 25,
            'description': '40ft High Cube container'
        }
    }

    @staticmethod
    def calculate_cbm(length_cm: float, width_cm: float, height_cm: float, quantity: int = 1) -> float:
        """
        Calculate Cubic Meter (CBM) for an item
        Formula: (length × width × height) / 1,000,000 × quantity
        """
        if not all([length_cm, width_cm, height_cm]):
            return 0.0

        # Convert cm to meters and calculate volume
        volume_per_item = (length_cm / 100) * (width_cm / 100) * (height_cm / 100)
        total_cbm = volume_per_item * quantity

        return round(total_cbm, 3)

    @staticmethod
    def calculate_pallet_count(total_cbm: float, pallet_capacity_cbm: float = 2.0) -> int:
        """
        Calculate number of pallets needed based on CBM
        Default pallet capacity is 2.0 CBM (standard pallet size)
        """
        if total_cbm <= 0 or pallet_capacity_cbm <= 0:
            return 0

        pallets_needed = math.ceil(total_cbm / pallet_capacity_cbm)
        return pallets_needed

    def recommend_truck_container(self, total_weight_kg: float, total_cbm: float,
                                pallet_count: int) -> Dict[str, Any]:
        """
        Recommend the most appropriate truck/container based on weight, CBM, and pallet count

        Returns:
            {
                'recommended': str,  # Truck/container type
                'alternatives': List[str],  # Alternative options
                'reasoning': str,  # Explanation for recommendation
                'capacity_utilization': Dict  # Utilization percentages
            }
        """
        if total_weight_kg <= 0 or total_cbm <= 0:
            return {
                'recommended': None,
                'alternatives': [],
                'reasoning': 'Invalid weight or CBM values',
                'capacity_utilization': {}
            }

        # Find suitable options
        suitable_options = []
        for truck_type, specs in self.TRUCK_CAPACITIES.items():
            if (total_weight_kg <= specs['max_weight_kg'] and
                total_cbm <= specs['max_cbm'] and
                pallet_count <= specs['max_pallets']):
                suitable_options.append(truck_type)

        if not suitable_options:
            return {
                'recommended': None,
                'alternatives': [],
                'reasoning': 'Load exceeds capacity of all available trucks/containers',
                'capacity_utilization': {}
            }

        # Prioritize by efficiency (choose smallest suitable option)
        priority_order = ['3ton', '5ton', '8ton', '20gp', '40hc']
        recommended = None

        for truck_type in priority_order:
            if truck_type in suitable_options:
                recommended = truck_type
                break

        # Calculate utilization for recommended option
        specs = self.TRUCK_CAPACITIES[recommended]
        utilization = {
            'weight_percent': round((total_weight_kg / specs['max_weight_kg']) * 100, 1),
            'cbm_percent': round((total_cbm / specs['max_cbm']) * 100, 1),
            'pallet_percent': round((pallet_count / specs['max_pallets']) * 100, 1)
        }

        # Generate reasoning
        reasoning_parts = []
        if utilization['weight_percent'] > 90:
            reasoning_parts.append("high weight utilization")
        elif utilization['weight_percent'] < 50:
            reasoning_parts.append("low weight utilization - consider smaller option")

        if utilization['cbm_percent'] > 90:
            reasoning_parts.append("high volume utilization")
        elif utilization['cbm_percent'] < 50:
            reasoning_parts.append("low volume utilization")

        reasoning = f"Recommended {recommended} ({specs['description']})"
        if reasoning_parts:
            reasoning += f" - {', '.join(reasoning_parts)}"

        return {
            'recommended': recommended,
            'alternatives': [opt for opt in suitable_options if opt != recommended],
            'reasoning': reasoning,
            'capacity_utilization': utilization,
            'specs': specs
        }

    def compute_cbm_pallet_truck(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to compute CBM, pallet count and truck recommendation from invoice data

        Expected invoice_data structure:
        {
            'length_cm': float or list,
            'width_cm': float or list,
            'height_cm': float or list,
            'pcs': int or list,
            'gross_weight_kg': float or list,
            ...
        }
        """
        # Extract dimensions and quantities
        lengths = self._extract_values(invoice_data.get('length_cm', []))
        widths = self._extract_values(invoice_data.get('width_cm', []))
        heights = self._extract_values(invoice_data.get('height_cm', []))
        quantities = self._extract_values(invoice_data.get('pcs', []))
        weights = self._extract_values(invoice_data.get('gross', []))

        # Calculate totals
        total_cbm = 0.0
        total_weight = 0.0

        # Calculate CBM for each item
        max_items = max(len(lengths), len(widths), len(heights), len(quantities))
        for i in range(max_items):
            length = lengths[i] if i < len(lengths) else 0
            width = widths[i] if i < len(widths) else 0
            height = heights[i] if i < len(heights) else 0
            qty = quantities[i] if i < len(quantities) else 1

            if length and width and height:
                item_cbm = self.calculate_cbm(length, width, height, qty)
                total_cbm += item_cbm

        # Calculate total weight
        for weight in weights:
            if weight:
                total_weight += weight

        # Calculate pallet count (assuming 2.0 CBM per pallet)
        pallet_count = self.calculate_pallet_count(total_cbm)

        # Get truck/container recommendation
        recommendation = self.recommend_truck_container(total_weight, total_cbm, pallet_count)

        return {
            'total_cbm': round(total_cbm, 3),
            'total_weight_kg': round(total_weight, 2),
            'pallet_count': pallet_count,
            'truck_recommendation': recommendation
        }

    def _extract_values(self, data) -> list:
        """Extract numeric values from various data formats"""
        if isinstance(data, list):
            return [float(x) if x is not None and str(x).strip() and str(x).replace('.', '').isdigit() else 0
                   for x in data]
        elif data is not None and str(data).strip() and str(data).replace('.', '').isdigit():
            return [float(data)]
        else:
            return [0]