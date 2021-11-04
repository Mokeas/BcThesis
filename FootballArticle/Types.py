# Brief description:

# collection of Enum classes for distinguishing types of entities
# e.g. class Result which types are win/draw/loss

# -----------------------------------------------------
# Python's libraries
from enum import Enum

# Other parts of the code
# -----------------------------------------------------


class Result(Enum):
    # always in home's team perspective
    WIN = 1
    DRAW = 0
    LOSS = 2


class Team(Enum):
    HOME = 0
    AWAY = 1


class Incident(Enum):
    GOAL = 0
    PENALTY_KICK = 1
    CARD = 2
    SUBSTITUTION = 3


class Card(Enum):
    YELLOW = 0
    RED_AUTO = 1
    RED_INSTANT = 2


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
    class Case(Enum):
        Nom = 1
        Gen = 2
        Dat = 3
        Acc = 4
        Vok = 5
        Loc = 6
        Ins = 7

    class Tense(Enum):
        Past = 0
        Pres = 1
        Fut = 2


class Constituent(Enum):
    ENTITY = 0
    VERB = 1
    WORD = 2
