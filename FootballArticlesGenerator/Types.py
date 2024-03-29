"""Collection of Enum classes for distinguishing types of entities."""

# Python's libraries
from enum import Enum


class Result(Enum):
    WIN = 1
    DRAW = 0
    LOSS = 2


class Team(Enum):
    HOME = 0
    AWAY = 1


class Incident(Enum):
    GOAL = 0
    PENALTY_KICK = 1   # penalty kick may also be missed and yet it is huge piece of information
    CARD = 2
    SUBSTITUTION = 3


class Card(Enum):
    YELLOW = 0
    RED_INSTANT = 1
    RED_AUTO = 2
    """Automatic red card after 2 yellows."""


class Goal(Enum):
    PENALTY = 0
    ASSISTANCE = 1
    SOLO_PLAY = 2
    OWN_GOAL = 3


class Message(Enum):
    GOAL = 0
    PENALTY_KICK_MISSED = 1
    CARD = 2
    SUBSTITUTION = 3
    RESULT = 4


class MessageSubtype(Enum):
    WIN = 0
    DRAW = 1
    LOSS = 2
    RED_INSTANT = 3
    RED_AUTO = 4
    YELLOW = 5
    ASSISTANCE = 6
    PENALTY = 7
    SOLO_PLAY = 8
    OWN_GOAL = 9


class Morph:
    """Morphological types used for better conversion when entering them into templates."""
    class Case(Enum):
        Nom = 1
        Gen = 2
        Dat = 3
        Acc = 4
        Voc = 5
        Loc = 6
        Ins = 7

    class Tense(Enum):
        Past = 0
        Pres = 1
        Fut = 2

    class Gender(Enum):
        MascA = 0   # masculine animate
        MascI = 1   # masculine inanimate
        Fem = 2
        Neut = 3


class Constituent(Enum):
    ENTITY = 0
    VERB = 1
    WORD = 2


class ExplicitEntityData(Enum):
    """Explicit data types that need to be specified in a template."""
    PARTICIPANT = 0
    PARTICIPANT_IN = 1
    PARTICIPANT_OUT = 2
    ASSISTANCE = 3
    TIME = 4
    SCORE = 5
    CURRENT_SCORE = 6
    TEAM_HOME = 7
    TEAM_AWAY = 8
