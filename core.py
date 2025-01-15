"""
Here we define the core components of the OLA engine.
"""
import random
import logging
import copy
import time

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


def get_hex_uppercase_string(number: int):
    """
    This is for saving print space for pieces with ranks above 9.
    """
    hex_string = hex(number)[2:].upper()

    return hex_string


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

    @staticmethod
    def get_piece_affiliation(piece: int):
        """
        This identifies whether a piece belongs to the blue or red player.
        """
        affiliation = None  # Initialize return value
        if Ranking.FLAG <= piece <= Ranking.SPY:
            affiliation = Player.BLUE
        elif Ranking.FLAG + Ranking.SPY <= piece <= Ranking.SPY*2:
            affiliation = Player.RED
        return affiliation

    @staticmethod
    def label_piece_by_team(piece: int):
        """
        This method returns the string that will be printed in the terminal to
        represent the piece.
        """
        labelled_piece = None  # Initialize return value
        if Board.get_piece_affiliation(piece) == Player.BLUE:
            labelled_piece = "b" + get_hex_uppercase_string(piece)
        elif Board.get_piece_affiliation(piece) == Player.RED:
            labelled_piece = "r" + get_hex_uppercase_string(
                piece - Ranking.SPY)

        return labelled_piece

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
                labelled_entry = self.label_piece_by_team(piece=entry)
                if entry == Ranking.BLANK:
                    self._print_blank_square()
                elif entry == blue_flag and pov == POV.WORLD and with_color:
                    self._print_square(self._get_colored(labelled_entry, blue))
                elif entry == red_flag and pov == POV.WORLD and with_color:
                    self._print_square(self._get_colored(labelled_entry, red))
                elif pov == POV.WORLD:
                    # Prints two chars wide
                    self._print_square(f"{labelled_entry:2}")
            print()  # Moves the next row to the next line
        self._print_column_numbers()
        print()  # Move the output after the board to a new line

    def piece_not_found(self, piece: int):
        """
        This checks if a particular piece is missing in the board's matrix.
        """
        return not any(piece in row for row in self.matrix)

    @staticmethod
    def has_at_edge_column(column_number: int):
        """
        This checks if a given column number is at the leftmost or rightmost
        edge of the board.
        """
        leftmost_column_number = 0
        rightmost_column_number = Board.COLUMNS - 1
        return (column_number in (leftmost_column_number,
                                  rightmost_column_number))

    @staticmethod
    def is_vacant_to_the_right(column_number: int, end_row: list[int]):
        """
        Checks if the square to the right of a given column in a row is blank.
        """
        go_right = 1
        return not end_row[column_number + go_right]

    @staticmethod
    def is_vacant_to_the_left(column_number: int, end_row: list[int]):
        """
        Checks if the square to the left of a given column in a row is blank.
        """
        go_left = -1
        return not end_row[column_number + go_left]

    @staticmethod
    def has_none_adjacent(column_number: int, end_row: list[int]):
        """
        This checks if a given column in a row has blank square neighbors.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        has_adjacent = False  # Initialize return value
        leftmost_column_number = 0
        rightmost_column_number = Board.COLUMNS - 1
        if (Board.has_at_edge_column(column_number)
            and column_number == leftmost_column_number
                and Board.is_vacant_to_the_right(column_number, end_row)):
            has_adjacent = True
        elif (Board.has_at_edge_column(column_number)
              and column_number == rightmost_column_number
              and Board.is_vacant_to_the_left(column_number, end_row)):
            has_adjacent = True
        elif (not Board.has_at_edge_column(column_number)
              and Board.is_vacant_to_the_right(column_number, end_row)
              and Board.is_vacant_to_the_left(column_number, end_row)):
            has_adjacent = True

        return has_adjacent

    def is_terminal(self):
        """
        This determines if the current game state is a terminal state.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        terminality = False  # Initialize return value

        blue_flag = Ranking.FLAG
        red_flag = Ranking.FLAG + Ranking.SPY  # See ranking class for details
        if (self.piece_not_found(blue_flag) or self.piece_not_found(red_flag)):
            terminality = True
            return terminality

        blue_end = 0
        red_end = -1  # The first and last row numbers, respectively
        if blue_flag in self.matrix[red_end] and self.blue_anticipating:
            # If the flag has already survived a turn in the board's red end
            terminality = True
        elif blue_flag in self.matrix[red_end] and not self.blue_anticipating:
            flag_column_number = self.matrix[red_end].index(blue_flag)
            terminality = Board.has_none_adjacent(flag_column_number,
                                                  self.matrix[red_end])
        elif red_flag in self.matrix[blue_end] and self.red_anticipating:
            # If the flag has already survived a turn in the board's blue end
            terminality = True
        elif red_flag in self.matrix[blue_end] and not self.red_anticipating:
            terminality = Board.has_none_adjacent(flag_column_number,
                                                  self.matrix[blue_end])
        else:
            terminality = False

        return terminality

    @staticmethod
    def get_piece_range(player: int):
        """
        This obtains the highest and lowest possible value representations of a 
        player's pieces.
        """
        blue_flag, blue_spy, red_flag, red_spy = (
            Ranking.FLAG, Ranking.SPY, Ranking.FLAG + Ranking.SPY,
            Ranking.SPY*2
        )  # See Ranking class for details
        piece_range_start, piece_range_end = (
            (blue_flag, blue_spy) if player == Player.BLUE
            else (red_flag, red_spy)
        )

        return piece_range_start, piece_range_end

    def not_allied_piece(self, entry: int):
        """
        This checks if the given board entry does not contain an allied piece of
        the player to move.
        """
        piece_range_start, piece_range_end = Board.get_piece_range(
            self.player_to_move)
        return (
            not (piece_range_start <= entry <= piece_range_end)
            or entry == Ranking.BLANK)

    def is_allied_piece(self, entry: int):
        """
        This checks if the given board entry contains an allied piece of the 
        player to move.
        """
        return not self.not_allied_piece(entry)

    def actions(self):
        """
        This enumerates the possible actions of the player to move in the game
        state.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        valid_actions = []  # Initialize return value
        bottom_row_number = leftmost_column_number = 0

        for row in range(Board.ROWS):
            for column in range(Board.COLUMNS):
                entry = self.matrix[row][column]
                # Define change in coordinates per direction (up, down, left,
                # and right)
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for direction in directions:
                    direction_row, direction_column = direction
                    new_row, new_column = (row + direction_row,
                                           column + direction_column)

                    if (bottom_row_number <= new_row < Board.ROWS
                        and leftmost_column_number <= new_column < Board.COLUMNS
                        and entry != Ranking.BLANK
                        and self.is_allied_piece(entry)
                            and self.not_allied_piece(
                                self.matrix[new_row][new_column])):
                        valid_actions.append(
                            f"{row}{column}{new_row}{new_column}")

        return valid_actions

    @staticmethod
    def remove_piece(board_matrix: list[list[int]], row: int,
                     column: int):
        """
        This removes a piece entry from a given board matrix.
        """
        board_matrix[row][column] = Ranking.BLANK

        return board_matrix

    def arbitrate_challenge(self, new_matrix: list[list[int]],
                            action: str, challenger_value: int,
                            target_value: int):
        """
        This reflects challenge moves in a new matrix by arbitrating the
        relative values of the opposing pieces.
        """
        starting_row, starting_column, destination_row, destination_column = (
            map(int, action)
        )
        if challenger_value == Ranking.PRIVATE and target_value == Ranking.SPY:
            new_matrix = self.move_piece_in_matrix_copy(new_matrix, action)
            return new_matrix

        if challenger_value == Ranking.SPY and target_value == Ranking.PRIVATE:
            new_matrix = self.remove_piece(new_matrix, starting_row,
                                           starting_column)
            return new_matrix

        if (challenger_value > target_value
            or (challenger_value == Ranking.FLAG
                and target_value == Ranking.FLAG)):
            new_matrix = self.move_piece_in_matrix_copy(new_matrix, action)
        elif challenger_value < target_value:
            new_matrix = self.remove_piece(new_matrix, starting_row,
                                           starting_column)
            return new_matrix
        elif challenger_value == target_value:
            new_matrix = self.remove_piece(new_matrix, starting_row,
                                           starting_column)
            new_matrix = self.remove_piece(new_matrix, destination_row,
                                           destination_column)
            return new_matrix

        return new_matrix

    def move_piece_in_matrix_copy(self, new_matrix: list[list[int]],
                                  action: str):
        """
        This reflects non-challenge moves in a new matrix by moving the selected
        piece in the presumably unoccupied destination square.
        """

        starting_row, starting_column, destination_row, destination_column = (
            map(int, action)
        )
        new_matrix[destination_row][destination_column] = (
            self.matrix[starting_row][starting_column])
        new_matrix[starting_row][starting_column] = Ranking.BLANK

        return new_matrix

    def transition(self, action: str):
        """
        This determines the next state based on the current state and the chosen
        action.
        """
        # Initialize the new game state
        new_matrix = copy.deepcopy(self.matrix)
        starting_row, starting_column, destination_row, destination_column = (
            map(int, action)
        )
        piece_to_move = self.matrix[starting_row][starting_column]
        destination_square = self.matrix[destination_row][destination_column]

        if destination_square == Ranking.BLANK:
            new_matrix = self.move_piece_in_matrix_copy(new_matrix, action)
        elif self.player_to_move == Player.BLUE:
            # The Ranking.SPY offset allows the flattening of the board state
            # (see Ranking class for more details).
            red_piece_value = destination_square - Ranking.SPY
            new_matrix = self.arbitrate_challenge(new_matrix, action,
                                                  piece_to_move, red_piece_value
                                                  )
        elif self.player_to_move == Player.RED:
            red_piece_value = piece_to_move - Ranking.SPY
            new_matrix = self.arbitrate_challenge(new_matrix, action,
                                                  red_piece_value,
                                                  destination_square
                                                  )
        blue_flag, red_flag = Ranking.FLAG, Ranking.FLAG + Ranking.SPY
        next_to_move = (
            Player.RED if self.player_to_move == Player.BLUE else Player.BLUE)
        blue_anticipating = red_anticipating = False
        if (blue_flag in self.matrix[-1] and not self.blue_anticipating
            and not self.has_none_adjacent(
                self.matrix[-1].index(blue_flag), self.matrix[-1])):
            blue_anticipating = True
        elif (red_flag in self.matrix[0] and not self.red_anticipating
              and not self.has_none_adjacent(
                  self.matrix[0].index(0), self.matrix[0]
        )):
            red_anticipating = True

        return Board(new_matrix, next_to_move, blue_anticipating,
                     red_anticipating)


class Controller:
    """
    This class contains constants that set a MatchSimulator's input (game move)
    sources.
    """
    HUMAN = 0
    RANDOM = 1

    def __init__(self):
        pass


class MatchSimulator:
    """
    This class handles the simulation of a GG match.
    """

    def __init__(self, blue_formation: list[int], red_formation: list[int],
                 controllers: list[int], save_data: bool):
        """
        The controllers parameter sets whether a human or an algorithm chooses 
        the moves for either or both sides of the simulated match (see constant 
        definitions in the Controller class).
        """
        self.blue_formation = blue_formation
        self.red_formation = self._place_in_red_range(red_formation)
        self.player_one = controllers[0]
        self.player_two = controllers[1]
        self.player_one_color = random.choice([Player.BLUE, Player.RED])
        self.player_two_color = Player.RED if (
            self.player_one_color == Player.BLUE) else Player.BLUE
        self.save_data = save_data
        self.game_history = []

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

    @staticmethod
    def _print_game_status(turn_number: int, arbiter_board: Board):
        print(f"Turn Number: {turn_number}")
        arbiter_board.print_state(POV.WORLD, with_color=True)
        print(f"Player to move: {arbiter_board.player_to_move}")

    def get_current_controller(self, board: Board):
        """
        This determines the source of moves of the MatchSimulator.
        """
        current_controller = None  # Initialize return value
        if board.player_to_move == self.player_one_color:
            current_controller = self.player_one
        elif board.player_to_move == self.player_two_color:
            current_controller = self.player_two

        return current_controller

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
        if self.save_data:
            self.game_history.append(arbiter_board.matrix)

        # TODO: Initialize initial blue and red infostates

        turn_number = 1
        branches_encountered = 0
        while not arbiter_board.is_terminal():
            MatchSimulator._print_game_status(turn_number, arbiter_board)
            valid_actions = arbiter_board.actions()
            branches_encountered += len(valid_actions)

            action = ""  # Initialize variable for storing chosen action
            if self.get_current_controller(arbiter_board) == Controller.RANDOM:
                action = random.choice(valid_actions)
            elif self.get_current_controller(arbiter_board) == Controller.HUMAN:
                while action not in valid_actions:
                    action = input("Choose a move: ")

            print(f"Chosen Move: {action}")

            if self.save_data:
                self.game_history.append(action)

            arbiter_board = arbiter_board.transition(action)
            turn_number += 1
