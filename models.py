from enum import IntEnum, auto


class ClockAction(IntEnum):
    In = auto()
    Out = auto()


class ClockStatus(IntEnum):
    In = auto()
    Out = auto()
    Unknown = auto()
