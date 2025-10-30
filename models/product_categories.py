"""
Product Category System - ARCH-20251029-002
Replaces window-only constraint with flexible category-based architecture
"""
from enum import Enum

class ProductCategory(str, Enum):
    """Product categories for architectural joinery"""
    WINDOW = "window"
    DOOR = "door"
    LOUVER_DOOR = "louver_door"
    RAILING = "railing"
    CURTAIN_WALL = "curtain_wall"
    SKYLIGHT = "skylight"
    CANOPY = "canopy"
    STANDALONE_MATERIAL = "standalone_material"

class DoorType(str, Enum):
    """Door types for DOOR and LOUVER_DOOR categories"""
    SINGLE_LEAF = "single_leaf"
    DOUBLE_LEAF = "double_leaf"
    SLIDING = "sliding"
    SWING = "swing"
    PIVOT = "pivot"
    FOLDING = "folding"
