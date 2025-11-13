from enum import Enum

class IconType(Enum):
    NONE = "none"
    ENTRANCE = "entrance"
    CHEST = "chest"
    LOCKED_DOOR = "door"
    STAIRS_UP = "stairs_up"
    STAIRS_DOWN = "stairs_down"
    BOSS = "boss"
    NPC = "npc"
    SWITCH = "switch"
    TRAP = "trap"
    SAVE_POINT = "save"

class Cell:
    """Represents a single cell on the grid."""
    def __init__(self, explored=False, icon=None, label="", locked=False):
        self.explored = explored
        self.icon = icon if icon is not None else IconType.NONE
        self.label = label
        self.locked = locked