"""
Here we define the core components of the OLA engine.
"""
import random
import logging

# Configure the logging
logging.basicConfig(level=logging.WARNING)


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

    @staticmethod
    def get_sensible_random_formation(piece_list: list[int]):
        """
        This is to ensure that the sampled random formation does not have the
        flag in the front line.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # Sample initial formation
        formation = Player.get_random_formation(piece_list)
        # The front line pieces are listed first in the formation
        front_line = formation[:Board.COLUMNS]

        while Ranking.FLAG in front_line:
            formation = Player.get_random_formation(piece_list)
            front_line = formation[:Board.COLUMNS]

        logger.setLevel(logging.DEBUG)
        logger.debug(formation)
        logger.debug(formation.index(Ranking.FLAG))

        return formation


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

    @staticmethod
    def _get_colored(text: str, color_code: str):
        """
        This helper method attaches a color code to the provided text string to
        embue the text with color when printed in the terminal.
        """
        return f"\033[{color_code}m{text:2}\033[0m"

    @staticmethod
    def _print_number_of_row(i: int):
        """
        This is for labelling the row with its number.
        """
        print(f"{i:2}", end='  ')

    @staticmethod
    def _print_square(contents: str):
        """
        This is for printing the contents of a square on the board.
        """
        print(contents, end=' ')

    @staticmethod
    def _print_blank_square():
        """
        This is for representing blank squares in the printed board.
        """
        Board._print_square(" -")

    @staticmethod
    def _print_column_numbers():
        """
        This is for printing the column numbers below the board.
        """
        print("\n    ", end='')
        for k in range(Board.COLUMNS):
            print(f"{k:2}", end=' ')

    def print_state(self, pov: int, with_color: bool):
        """
        This displays the state represented by the Board instance to the 
        terminal. The pov parameter determines which of the pieces have visible
        rank numbers (see constant definitions in POV class). The with_color 
        parameter determines whether the blue and red flags are colored 
        appropriately for easier identification. 
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # Color codes for printing colored text
        blue = "34"
        red = "31"

        # Shorthands for piece rankings
        blue_flag = Ranking.FLAG
        red_flag = Ranking.FLAG + Ranking.SPY  # See Ranking class for details

        print()  # Starts the board to a new line
        for i, row in enumerate(self.matrix):
            self._print_number_of_row(i)
            for entry in row:
                if entry == Ranking.BLANK:
                    self._print_blank_square()
                elif entry == blue_flag and pov == POV.WORLD and with_color:
                    self._print_square(self._get_colored(entry, blue))
                elif entry == red_flag and pov == POV.WORLD and with_color:
                    self._print_square(self._get_colored(entry, red))
                elif pov == POV.WORLD:
                    self._print_square(f"{entry:2}")  # Prints two chars wide
            print()  # Moves the next row to the next line
        self._print_column_numbers()
        print()  # Move the output after the board to a new line


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
        self.red_formation = self._place_in_red_range(red_formation)
        self.mode = mode
        self.save_data = save_data

    @staticmethod
    def _place_in_red_range(formation: list[int]):
        """
        This is to ensure that the red player's pieces are between 16 and 30 
        (see Ranking class for details).
        """

        for i, entry in enumerate(formation):
            if entry > Ranking.BLANK:
                formation[i] += Ranking.SPY

        return formation

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

        arbiter_board.print_state(POV.WORLD, with_color=True)
