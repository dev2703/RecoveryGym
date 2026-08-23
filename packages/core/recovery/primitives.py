from __future__ import annotations

from enum import Enum


class RecoveryPrimitive(str, Enum):
    STOP = "STOP"
    SAFE_STOP = "SAFE_STOP"
    MOVE_TO_OBJECT = "MOVE_TO_OBJECT"
    REGRASP = "REGRASP"
    VERIFY_GRASP = "VERIFY_GRASP"
    RESUME = "RESUME"
    REALIGN = "REALIGN"
    VERIFY_TARGET = "VERIFY_TARGET"
