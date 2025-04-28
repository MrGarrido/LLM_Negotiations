"""
Constants for the V5_garrido_negotiations system.
"""

import re
from typing import Dict, List, Any

class Constants:
    """Constants for the negotiation system."""
    
    # Roles
    ROLE_BUYER = 'buyer'
    ROLE_SUPPLIER = 'supplier'
    ROLES = [ROLE_SUPPLIER, ROLE_BUYER]
    
    # Price and quality ranges
    PRICE_RANGE = range(1, 15)
    QUALITY_RANGE = range(0, 5)
    
    # Patterns for extracting offers and constraints
    PATTERN_OFFER = re.compile(r'\[([^\]]+)\]')
    PATTERN_CONSTRAINT = re.compile(r'\[(\d+)\]')
    
    @staticmethod
    def opposite(role: str) -> str:
        """Get the opposite role."""
        return Constants.ROLE_BUYER if role == Constants.ROLE_SUPPLIER else Constants.ROLE_SUPPLIER

# Create a global instance for easy access
C = Constants()

# Configuration type
Config = Dict[str, Any]
