from dataclasses import dataclass


@dataclass
class Colors:
    TEXT: tuple = (255, 255, 255)
    HIGHLIGHT: tuple = (0, 255, 0)
    LINE: tuple = (0, 255, 255)
    ERROR: tuple = (0, 0, 255)
