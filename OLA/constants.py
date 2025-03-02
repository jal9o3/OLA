"""
This contains abstracted constant definitions for GG.
"""


class Ranking:
    """
    This class contains constants related to the designation of piece rankings.
    """
    # PIECE RANKINGS
    BLANK = 0
    # To reduce the dimensionality of the board matrix,
    # blue pieces are represented as is (1 to 15)
    # and red pieces are represented as Rank + 15
    FLAG = 1
    PRIVATE = 2
    SERGEANT = 3
    SECOND_LIEUTENANT = 4
    FIRST_LIEUTENANT = 5
    CAPTAIN = 6
    MAJOR = 7
    LIEUTENANT_COLONEL = 8
    COLONEL = 9
    BRIGADIER_GENERAL = 10
    MAJOR_GENERAL = 11
    LIEUTENANT_GENERAL = 12
    GENERAL = 13
    GENERAL_OF_THE_ARMY = 14
    SPY = 15
    UNKNOWN_BLUE_PIECE = 31
    UNKNOWN_RED_PIECE = 32

    INITIAL_PIECES = {
        FLAG, PRIVATE, PRIVATE, PRIVATE, PRIVATE, PRIVATE, PRIVATE, SERGEANT,
        SECOND_LIEUTENANT, FIRST_LIEUTENANT, CAPTAIN, MAJOR, LIEUTENANT_COLONEL,
        COLONEL, BRIGADIER_GENERAL, MAJOR_GENERAL, LIEUTENANT_GENERAL, GENERAL,
        GENERAL_OF_THE_ARMY, SPY, SPY
    }

    # Formations can be sampled by shuffling this list
    SORTED_FORMATION = [
        BLANK, BLANK, BLANK, BLANK, BLANK, BLANK,
        FLAG, PRIVATE, PRIVATE, PRIVATE, PRIVATE, PRIVATE, PRIVATE, SERGEANT,
        SECOND_LIEUTENANT, FIRST_LIEUTENANT, CAPTAIN, MAJOR, LIEUTENANT_COLONEL,
        COLONEL, BRIGADIER_GENERAL, MAJOR_GENERAL, LIEUTENANT_GENERAL, GENERAL,
        GENERAL_OF_THE_ARMY, SPY, SPY
    ]

    def __init__(self):
        pass


class POV:
    """
    This class contains constants for the possible board printing POVs.
    """

    WORLD = 0
    BLUE = 1
    RED = 2

    def __init__(self):
        pass


class Result:
    """
    This class contains constants that represent the possible results of actions
    in game states, for use with infostates.
    """

    DRAW = 0
    WIN = 1
    OCCUPY = 2
    LOSS = 3

    def __init__(self):
        pass


class Controller:
    """
    This class contains constants that set a MatchSimulator's input (game move)
    sources.
    """
    HUMAN = 0
    RANDOM = 1

    def __init__(self):
        pass
