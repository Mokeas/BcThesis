"""Collection of Enum classes for distinguishing types of entities."""

# Python's libraries
from enum import Enum


class Result(Enum):
    """Result always in home's team perspective."""
    WIN = 1
    DRAW = 0
    LOSS = 2


class Team(Enum):
    """Types of team - home or away."""
    HOME = 0
    AWAY = 1


class Incident(Enum):
    """Types of incident - goal, penalty kick, card, substitution."""
    GOAL = 0
    PENALTY_KICK = 1   # penalty kick may also be missed and yet it is huge piece of information
    CARD = 2
    SUBSTITUTION = 3


class Card(Enum):
    """Types of card - yellow and two for red - instant or automatic after 2 yellows."""
    YELLOW = 0
    RED_AUTO = 1
    RED_INSTANT = 2


class Goal(Enum):
    """Types of goal - penalty, goal with/without assistance and own goal."""
    PENALTY = 0
    ASSISTANCE = 1
    SOLO_PLAY = 2
    OWN_GOAL = 3


class Message(Enum):
    """Types of messages - goal, missed penalty kick, card, substitution, result."""
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
        """Types of cases - 7 in czech language."""
        Nom = 1
        Gen = 2
        Dat = 3
        Acc = 4
        Vok = 5
        Loc = 6
        Ins = 7

    class Tense(Enum):
        """Types of tenses - past, present and future."""
        Past = 0
        Pres = 1
        Fut = 2


class Constituent(Enum):
    """Types of constituent in a sentence - entity, verb, word."""
    ENTITY = 0
    VERB = 1
    WORD = 2
