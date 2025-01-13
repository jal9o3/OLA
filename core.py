import random

def get_random_permutation(elements: list):
    list_to_shuffle = elements[:]
    random.shuffle(list_to_shuffle)
    shuffled_list = list_to_shuffle
    return tuple(shuffled_list)

class Player:
    def __init__(self, color: int):
        self.color = color
    
    def get_random_formation(piece_list: list[int]):
        return get_random_permutation(piece_list)

class Board:
    ROWS = 8
    COLUMNS = 9

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

    BLUE_PLAYER = 1
    RED_PLAYER = 2

    """
    The matrix is simply a representation of the current piece positions and
    ranks, with the rank designations being 0 to 30 (see constant definitions 
    above).

    blue_anticipating is True when the blue player's flag has reached the eighth
    row, but can still be challenged in the next turn by a red piece. If red 
    fails to challenge, blue wins. The same logic applies to red_anticipating,
    except that the red player's flag must reach the first row.
    """
    def __init__(self, matrix: list[list[int]], player_to_move: int, 
                 blue_anticipating: bool, red_anticipating: bool):
        self.player_to_move = player_to_move
        self.blue_anticipating = blue_anticipating
        self.red_anticipating = red_anticipating