"""
Here we define the core components of the OLA engine.
"""
import random
import logging


def get_random_permutation(elements: list):
    """
    This function receives a list and returns a shuffled copy of it.
    """
    list_to_shuffle = elements[:]
    random.shuffle(list_to_shuffle)
    shuffled_list = list_to_shuffle
    return tuple(shuffled_list)


def get_blank_matrix(rows: int, columns: int):
    """
    This function returns a matrix of the specified number of rows and columns,
    with all entries set to 0 (aka BLANK).
    """
    return [[Ranking.BLANK for col in range(columns)] for row in range(rows)]


class Player:
    """
    This class handles player related functionality such as sampling valid
    formations.
    """

    BLUE = 1
    RED = 2

    def __init__(self, color: int):
        self.color = color

    @staticmethod
    def get_random_formation(piece_list: list[int]):
        """
        This function receives a list of pieces and returns a shuffled copy of
        it. Ideally, it should receive Ranking.SORTED_FORMATION to obtain a
        random valid formation.
        """
        return get_random_permutation(piece_list)


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


class Board:
    """
    This class represents the current game state as seen by the arbiter.
    """
    ROWS = 8
    COLUMNS = 9

    def __init__(self, matrix: list[list[int]], player_to_move: int,
                 blue_anticipating: bool, red_anticipating: bool):
        """
        The matrix is simply a representation of the current piece positions and
        ranks, with the rank designations being 0 to 30 (see constant 
        definitions in the Ranking class).

        blue_anticipating is True when the blue player's flag has reached the 
        eighth row, but can still be challenged in the next turn by a red piece. 
        If red fails to challenge, blue wins. The same logic applies to 
        red_anticipating, except that the red player's flag must reach the 
        first row.
        """
        self.matrix = matrix
        self.player_to_move = player_to_move
        self.blue_anticipating = blue_anticipating
        self.red_anticipating = red_anticipating


class MatchSimulator:
    """
    This class handles the simulation of a GG match.
    """
    # TODO: Define the mode designations

    def __init__(self, blue_formation: list[int], red_formation: list[int],
                 mode: int, save_data: bool):
        """
        The mode parameter sets whether a human or an algorithm chooses the 
        moves for either or both sides of the simulated match (see constant 
        definitions in the (to be implemented) class).
        """
        self.blue_formation = blue_formation
        self.red_formation = red_formation
        self.mode = mode
        self.save_data = save_data

    @staticmethod
    def _prepare_empty_matrices():
        """
        This helper method prepares a blank starting matrix for each of the two
        players.
        """
        blue_player_matrix = get_blank_matrix(rows=Board.ROWS,
                                              columns=Board.COLUMNS)
        red_player_matrix = get_blank_matrix(rows=Board.ROWS,
                                             columns=Board.COLUMNS)

        return blue_player_matrix, red_player_matrix

    @staticmethod
    def _place_formation_on_matrix(formation: list[int],
                                   matrix: list[list[int]]):
        """
        The formation is placed on the first three rows of the player's side
        of the board. The formation list must enumerate from the furthermost
        row (from the player's perspective) to the nearest, from left to right.
        """
        i = 0
        for row in range(Board.ROWS-3, Board.ROWS):
            for column in range(Board.COLUMNS):
                if i < len(formation):
                    matrix[row][column] = formation[i]
                    i += 1

        return matrix

    @staticmethod
    def _flip_matrix(matrix: list[list[int]]):
        """
        This helper method is for placing the blue pieces in their starting
        positions from (0,0) to (2,8).
        """
        # Flip the matrix upside down
        matrix = matrix[::-1]
        # Flip each blue board row left to right
        matrix = [row[::-1] for row in matrix]

        return matrix

    @staticmethod
    def _combine_player_matrices(blue_player_matrix: list[list[int]],
                                 red_player_matrix: list[list[int]]):
        """
        This helper method is for joining the blue and red starting matrices
        into one matrix for the arbiter.
        """
        combined_matrix = [
            [blue_player_matrix[i][j] + red_player_matrix[i][j] for j in range(
                Board.COLUMNS)] for i in range(Board.ROWS)
        ]

        return combined_matrix

    def setup_arbiter_matrix(self):
        """
        This instance method takes the provided blue and red formations and
        returns a matrix for the arbiter that represents the initial game state.
        """
        blue_player_matrix, red_player_matrix = (
            MatchSimulator._prepare_empty_matrices()
        )
        blue_player_matrix = MatchSimulator._place_formation_on_matrix(
            self.blue_formation, blue_player_matrix)
        # The blue player's pieces must initially occupy from (0,0) to (2,8)
        blue_player_matrix = MatchSimulator._flip_matrix(blue_player_matrix)
        red_player_matrix = MatchSimulator._place_formation_on_matrix(
            self.red_formation, red_player_matrix)

        arbiter_matrix = MatchSimulator._combine_player_matrices(
            blue_player_matrix, red_player_matrix)

        return arbiter_matrix

    def start(self):
        """
        This method simulates a GG match in the terminal, either taking input
        from humans or choosing moves based on an algorithm or even both.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        arbiter_board = Board(self.setup_arbiter_matrix(),
                              player_to_move=Player.BLUE,
                              blue_anticipating=False, red_anticipating=False)

        return arbiter_board.matrix
