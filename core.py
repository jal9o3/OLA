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

    ARBITER = 0
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

    @staticmethod
    def get_flag_values():
        """
        This returns the shorthands for the flags, useful for a flattening the
        state representation.
        """
        blue_flag = Ranking.FLAG
        red_flag = Ranking.FLAG + Ranking.SPY  # See Ranking class for details

        return blue_flag, red_flag

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
        blue, red = "34", "31"

        # Shorthands for piece rankings
        blue_flag, red_flag = Board.get_flag_values()

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

        result = False  # Initialize return value
        leftmost_column_number = 0
        rightmost_column_number = Board.COLUMNS - 1
        if (Board.has_at_edge_column(column_number)
            and column_number == leftmost_column_number
                and Board.is_vacant_to_the_right(column_number, end_row)):
            result = True
        elif (Board.has_at_edge_column(column_number)
              and column_number == rightmost_column_number
              and Board.is_vacant_to_the_left(column_number, end_row)):
            result = True
        elif (not Board.has_at_edge_column(column_number)
              and Board.is_vacant_to_the_right(column_number, end_row)
              and Board.is_vacant_to_the_left(column_number, end_row)):
            result = True

        return result

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
        start_row, start_col, dest_row, dest_col = (
            map(int, action)
        )
        if challenger_value == Ranking.PRIVATE and target_value == Ranking.SPY:
            new_matrix = self.move_piece_in_matrix_copy(new_matrix, action)
            return new_matrix

        if challenger_value == Ranking.SPY and target_value == Ranking.PRIVATE:
            new_matrix = self.remove_piece(new_matrix, start_row,
                                           start_col)
            return new_matrix

        if (challenger_value > target_value
            or (challenger_value == Ranking.FLAG
                and target_value == Ranking.FLAG)):
            new_matrix = self.move_piece_in_matrix_copy(new_matrix, action)
        elif challenger_value < target_value:
            new_matrix = self.remove_piece(new_matrix, start_row,
                                           start_col)
            return new_matrix
        elif challenger_value == target_value:
            new_matrix = self.remove_piece(new_matrix, start_row,
                                           start_col)
            new_matrix = self.remove_piece(new_matrix, dest_row,
                                           dest_col)
            return new_matrix

        return new_matrix

    def move_piece_in_matrix_copy(self, new_matrix: list[list[int]],
                                  action: str):
        """
        This reflects non-challenge moves in a new matrix by moving the selected
        piece in the presumably unoccupied destination square.
        """

        start_row, start_col, dest_row, dest_col = (
            map(int, action)
        )
        new_matrix[dest_row][dest_col] = (
            self.matrix[start_row][start_col])
        new_matrix[start_row][start_col] = Ranking.BLANK

        return new_matrix

    def transition(self, action: str, *args, **kwargs):
        """
        This determines the next state based on the current state and the chosen
        action.
        """
        _, _ = args, kwargs  # Stops the linter's complaints

        # Initialize the new game state
        new_matrix = copy.deepcopy(self.matrix)
        start_row, start_col, dest_row, dest_col = (
            map(int, action)
        )
        piece_to_move = self.matrix[start_row][start_col]
        destination_square = self.matrix[dest_row][dest_col]

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
        player_anticipations = [False, False]  # Blue and red respectively
        if (blue_flag in self.matrix[-1] and not self.blue_anticipating
            and not self.has_none_adjacent(
                self.matrix[-1].index(blue_flag), self.matrix[-1])):
            player_anticipations[0] = True
        elif (red_flag in self.matrix[0] and not self.red_anticipating
              and not self.has_none_adjacent(
                  self.matrix[0].index(0), self.matrix[0]
        )):
            player_anticipations[1] = True

        return Board(new_matrix, player_to_move=(
            Player.RED if self.player_to_move == Player.BLUE else Player.BLUE),
            blue_anticipating=player_anticipations[0],
            red_anticipating=player_anticipations[1])

    def deduce_action_result(self, matrix_difference: list[list[int]],
                             action: str):
        """
        This examines the characteristics of the difference matrix to classify
        the result of the action in the board state.
        """
        result = None  # Initialize return value
        start_row, start_col, dest_row, dest_col = (
            map(int, action)
        )
        challenger_value, target_value = (self.matrix[start_row][start_col],
                                          self.matrix[dest_row][dest_col])
        # Deduce the result based on the difference matrix' characteristics
        if (matrix_difference[start_row][start_col] == challenger_value
                and matrix_difference[dest_row][dest_col] == target_value):
            result = Result.DRAW
        elif (matrix_difference[start_row][start_col] == challenger_value
              and (matrix_difference[dest_row][dest_col] == (
                target_value - challenger_value
                  ) and self.matrix[dest_row][dest_col] == Ranking.BLANK)
              ):
            result = Result.OCCUPY
        elif (matrix_difference[start_row][start_col] == challenger_value
              and (matrix_difference[dest_row][dest_col] == (
                target_value - challenger_value
                  ) and self.matrix[dest_row][dest_col] != Ranking.BLANK)
              ):
            result = Result.WIN
        elif (matrix_difference[start_row][start_col] == challenger_value
                and matrix_difference[dest_row][dest_col] == Ranking.BLANK):
            result = Result.LOSS

        return result

    def classify_action_result(self, action: str, new_board: 'Board'):
        """
        This classifies action results as DRAW, WIN, LOSS (for challenge moves)
        or OCCUPY (for non-challenge moves), for use of the Infostate class'
        transition function.
        """
        matrix_difference = [
            [self.matrix[i][j] - new_board.matrix[i][j]
             for j in range(Board.COLUMNS)] for i in range(Board.ROWS)]

        return self.deduce_action_result(matrix_difference, action)

    def reward(self):
        """
        This assigns a numerical value to terminal states. Positive reward
        indicates a blue win, negative reward indicates a red win, and a zero
        indicates a draw.
        """

        blue_flag = Ranking.FLAG
        red_flag = Ranking.FLAG + Ranking.SPY  # See ranking class for details
        blue_end = 0
        red_end = -1  # The first and last row numbers, respectively
        win_value = 1000000

        reward = 0  # Initialize return value
        if self.piece_not_found(blue_flag):
            reward = -win_value
        elif self.piece_not_found(red_flag):
            reward = win_value
        elif blue_flag in self.matrix[red_end] and self.blue_anticipating:
            # If the flag has already survived a turn in the board's red end
            reward = win_value
        elif red_flag in self.matrix[blue_end] and self.red_anticipating:
            # If the flag has already survived a turn in the board's blue end
            reward = -win_value
        else:
            reward = 0  # Assume a draw

        return reward


class InfostatePiece:
    """
    This represents a piece on the infostate.
    """

    def __init__(self, color: int, rank_floor: int, rank_ceiling: int):
        self.color = color
        self.rank_floor = rank_floor
        self.rank_ceiling = rank_ceiling


class Infostate(Board):
    """
    This represents the current game state as seen by either of the players.
    """

    def __init__(self, abstracted_board: list[list[InfostatePiece]], owner: int,
                 player_to_move: int, anticipating=bool):
        """
        In contrast to the arbiter board, the infostate must belong to strictly
        one of the players, and the value of the anticipating attribute depends
        on the location of the infostate owner's flag.
        """
        super().__init__(matrix=None, player_to_move=player_to_move,
                         blue_anticipating=False, red_anticipating=False)
        self.owner = owner
        # Override attributes of the parent board class
        self.matrix = Infostate._to_matrix(infostate_board=abstracted_board)
        self.anticipating = anticipating
        self.abstracted_board = abstracted_board

    @staticmethod
    def _to_matrix(infostate_board: list[list[InfostatePiece]]):
        infostate_matrix = [[[0, 0] for col in range(Board.COLUMNS)]
                            for row in range(Board.ROWS)]
        for i, row in enumerate(infostate_board):
            for j, piece in enumerate(row):
                if piece.color == Player.BLUE:
                    infostate_matrix[i][j] = [piece.rank_floor,
                                              piece.rank_ceiling]
                elif piece.color == Player.RED:
                    infostate_matrix[i][j] = [piece.rank_floor + Ranking.SPY,
                                              piece.rank_ceiling + Ranking.SPY]

        return infostate_matrix

    @staticmethod
    def at_start(owner: int, board: Board) -> 'Infostate':
        """
        This creates the starting infostate for either of the players.
        """
        infostate_board = copy.deepcopy(board.matrix)  # Initialize the board
        opponent = (Player.RED if owner == Player.BLUE else Player.BLUE)
        offset = 0 if owner == Player.BLUE else Ranking.SPY  # For red pieces
        for i, row in enumerate(board.matrix):
            for j, entry in enumerate(row):
                # Set initial value bounds for the pieces
                if entry == Ranking.BLANK:
                    infostate_board[i][j] = InfostatePiece(
                        color=Player.ARBITER, rank_floor=Ranking.BLANK,
                        rank_ceiling=Ranking.BLANK)
                elif Infostate.get_piece_affiliation(piece=entry) == owner:
                    infostate_board[i][j] = InfostatePiece(
                        color=owner, rank_floor=entry - offset,
                        rank_ceiling=entry - offset
                    )
                elif Infostate.get_piece_affiliation(piece=entry) != owner:
                    infostate_board[i][j] = InfostatePiece(
                        color=opponent, rank_floor=Ranking.FLAG,
                        rank_ceiling=Ranking.SPY
                    )

        return Infostate(abstracted_board=infostate_board, owner=owner,
                         player_to_move=Player.BLUE, anticipating=False)

    @staticmethod
    def _print_blank_square():
        """
        This is for representing blank squares in the printed infostate.
        """
        Board._print_square("[-----]")

    @staticmethod
    def _print_column_numbers():
        """
        This is for printing the column numbers below the board.
        """
        print("\n ", end='')
        for k in range(Board.COLUMNS):
            print(f"{k:7}", end=' ')

    def print_state(self, *args, **kwargs):
        """
        This prints the state as seen by either of the players in the terminal.
        """
        _, _ = args, kwargs  # Stops the linter's complaints

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        print()  # Starts the board to a new line
        for i, row in enumerate(self.matrix):
            self._print_number_of_row(i)
            for entry in row:
                lowest_possible, highest_possible = entry[0], entry[1]
                # Label both sides of the entry range
                labelled_entry = [self.label_piece_by_team(
                    piece=lowest_possible),
                    self.label_piece_by_team(
                    piece=highest_possible)]
                if (highest_possible == Ranking.BLANK
                        and lowest_possible == Ranking.BLANK):
                    self._print_blank_square()
                else:
                    # Prints two chars wide
                    self._print_square(
                        f"({labelled_entry[0]},{labelled_entry[1]})")
            print("\n")  # Moves the next row to the next line
        self._print_column_numbers()
        print()  # Move the output after the board to a new line

        if self.anticipating:
            print("\n[WAITING IF OPPONENT CHALLENGES]\n")

    @staticmethod
    def _remove_piece(board: list[list[InfostatePiece]],
                      entry_location: tuple[int]):
        entry_row, entry_col = entry_location

        board[entry_row][entry_col] = InfostatePiece(color=Player.ARBITER,
                                                     rank_floor=Ranking.BLANK,
                                                     rank_ceiling=Ranking.BLANK)

        return board

    @staticmethod
    def _remove_pieces(board: list[list[InfostatePiece]],
                       locs: tuple[tuple[int]]):
        start_row, start_col = locs[0]
        dest_row, dest_col = locs[1]

        matrix = Infostate._remove_piece(board=board, entry_location=(
            start_row,
            start_col))
        matrix = Infostate._remove_piece(board=board, entry_location=(
            dest_row,
            dest_col
        ))
        return matrix

    def _move_piece(self, board: list[list[InfostatePiece]],
                    start: tuple[int], end: tuple[int]):
        """
        This reflects a move in an infostate in an infostate matrix.
        """
        start_row, start_col = start[0], start[1]
        dest_row, dest_col = end[0], end[1]

        board[dest_row][dest_col].rank_floor = board[
            start_row][start_col].rank_floor
        board[dest_row][dest_col].rank_ceiling = board[
            start_row][start_col].rank_ceiling
        board[dest_row][dest_col].color = board[start_row][
            start_col].color
        board[start_row][start_col] = InfostatePiece(color=Player.ARBITER,
                                                     rank_floor=Ranking.BLANK,
                                                     rank_ceiling=Ranking.BLANK)

        return board

    def _piece_is_owned(self, row: int, col: int):
        """
        Determines if the piece at the specified row and column in the infostate 
        belongs to the owner of the infostate.
        """
        return self.abstracted_board[row][col].color == self.owner

    @staticmethod
    def _update_val(board: list[list[InfostatePiece]], to_update: tuple[int],
                    source: tuple[int]):
        """
        This sets a new value to the range of an unidentified piece in a copy of 
        the infostate piece board. This value is calculated from the value of 
        the associated opposing piece involved in the action.
        """

        update_row, update_col, source_row, source_col = (to_update[0],
                                                          to_update[1],
                                                          source[0], source[1])

        # Deal with the SPY vs PRIVATE edge cases
        if board[source_row][source_col].rank_floor == Ranking.SPY:
            board[update_row][update_col].rank_floor = Ranking.PRIVATE
            board[update_row][update_col].rank_ceiling = Ranking.PRIVATE
        else:
            board[update_row][update_col].rank_floor = (
                board[source_row][source_col].rank_ceiling + 1)

        return board

    def _find_flag(self, board: list[list[InfostatePiece]]):
        """
        This finds the infostate owner's flag, useful for setting the
        anticipating attribute.
        """
        for i, row in enumerate(board):
            for j, piece in enumerate(row):
                if (piece.color == self.owner
                        and piece.rank_floor == Ranking.FLAG):
                    return (i, j)

        return None

    # TODO: Combine the next two methods into one

    @staticmethod
    def is_vacant_to_the_right(column_number: int,
                               end_row: list[InfostatePiece]):
        """
        Checks if the square to the right of a given column in a row is blank.
        """
        go_right = 1
        # The only squares "owned" by the arbiter are blank squares
        return end_row[column_number + go_right].color == Player.ARBITER

    @staticmethod
    def is_vacant_to_the_left(column_number: int,
                              end_row: list[InfostatePiece]):
        """
        Checks if the square to the left of a given column in a row is blank.
        """
        go_left = -1
        # The only squares "owned" by the arbiter are blank squares
        return end_row[column_number + go_left].color == Player.ARBITER

    @staticmethod
    def has_none_adjacent(column_number: int, end_row: list[InfostatePiece]):
        """
        This checks if a given column in a row has blank square neighbors.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        result = False  # Initialize return value
        leftmost_column_number = 0
        rightmost_column_number = Board.COLUMNS - 1
        if (Board.has_at_edge_column(column_number)
            and column_number == leftmost_column_number
                and Infostate.is_vacant_to_the_right(column_number, end_row)):
            result = True
        elif (Board.has_at_edge_column(column_number)
              and column_number == rightmost_column_number
              and Infostate.is_vacant_to_the_left(column_number, end_row)):
            result = True
        elif (not Board.has_at_edge_column(column_number)
              and Infostate.is_vacant_to_the_right(column_number, end_row)
              and Infostate.is_vacant_to_the_left(column_number, end_row)):
            result = True

        return result

    def transition(self, action: str, *args, **kwargs):
        """
        This obtains the next infostate based on the provided action and the
        result classification of the action.
        """
        _ = args  # Stops the linter's complaints
        new_board = copy.deepcopy(self.abstracted_board)
        start_row, start_col, dest_row, dest_col = (
            map(int, action)
        )
        # Find the action's result in the keyword arguments
        result = kwargs['result'] if 'result' in kwargs else None

        if result == Result.DRAW:
            new_board = Infostate._remove_pieces(board=new_board, locs=(
                (start_row, start_col), (dest_row, dest_col)))

        elif (result == Result.WIN
              and self._piece_is_owned(row=start_row, col=start_col)):
            new_board = self._move_piece(board=new_board, start=(
                start_row, start_col), end=(dest_row, dest_col))

        elif (result == Result.WIN
              and not self._piece_is_owned(row=start_row, col=start_col)):
            new_board = Infostate._update_val(board=new_board,
                                              to_update=(start_row, start_col),
                                              source=(dest_row, dest_col))
            new_board = self._move_piece(board=new_board, start=(
                start_row, start_col), end=(dest_row, dest_col))

        elif result == Result.OCCUPY:
            new_board = self._move_piece(board=new_board, start=(
                start_row, start_col), end=(dest_row, dest_col))

        elif (result == Result.LOSS
              and self._piece_is_owned(dest_row, dest_col)):
            new_board = Infostate._remove_piece(
                board=new_board, entry_location=(start_row, start_col))

        elif (result == Result.LOSS
              and not self._piece_is_owned(row=dest_row, col=dest_col)):
            new_board = Infostate._update_val(board=new_board,
                                              to_update=(dest_row, dest_col),
                                              source=(start_row, start_col))
            new_board = Infostate._remove_piece(
                board=new_board, entry_location=(start_row, start_col))

        anticipation = self.anticipating
        flag_loc = self._find_flag(board=new_board)
        if flag_loc is None:
            anticipation = False
        elif (self.owner == Player.BLUE and flag_loc[0] == Infostate.ROWS - 1
              and not self.anticipating
              and self.has_none_adjacent(column_number=flag_loc[1],
                                         end_row=new_board[-1])):
            anticipation = True
        elif (self.owner == Player.RED and flag_loc[0] == 0
              and not self.anticipating
              and self.has_none_adjacent(column_number=flag_loc[1],
                                         end_row=new_board[0])):
            anticipation = True

        return Infostate(abstracted_board=new_board, owner=self.owner,
                         player_to_move=(
                             Player.RED if self.player_to_move == Player.BLUE
                             else Player.BLUE), anticipating=anticipation)


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

    def __init__(self, formations: list[list[int]], controllers: list[int],
                 save_data: bool, pov: int):
        """
        The controllers parameter sets whether a human or an algorithm chooses
        the moves for either or both sides of the simulated match (see constant
        definitions in the Controller class).
        """
        self.blue_formation = formations[0]
        self.red_formation = self._place_in_red_range(formations[1])
        self.controllers = controllers
        self.player_one_color = random.choice([Player.BLUE, Player.RED])
        self.player_two_color = Player.RED if (
            self.player_one_color == Player.BLUE) else Player.BLUE
        self.save_data = save_data
        self.game_history = []
        self.pov = pov

    @ staticmethod
    def _place_in_red_range(formation: list[int]):
        """
        This is to ensure that the red player's pieces are between 16 and 30
        (see Ranking class for details).
        """

        for i, entry in enumerate(formation):
            if entry > Ranking.BLANK:
                formation[i] += Ranking.SPY

        return formation

    @ staticmethod
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

    @ staticmethod
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

    @ staticmethod
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

    @ staticmethod
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

    @ staticmethod
    def _print_game_status(turn_number: int, arbiter_board: Board,
                           infostates: list[Infostate], pov: int):

        blue_infostate, red_infostate = infostates[0], infostates[1]
        print(f"Turn Number: {turn_number}")
        if pov == POV.WORLD:
            arbiter_board.print_state(POV.WORLD, with_color=True)
        elif pov == POV.BLUE:
            blue_infostate.print_state()
        elif pov == POV.RED:
            red_infostate.print_state()

        print(f"Player to move: {arbiter_board.player_to_move}")

    def get_current_controller(self, board: Board):
        """
        This determines the source of moves of the MatchSimulator.
        """
        current_controller = None  # Initialize return value
        if board.player_to_move == self.player_one_color:
            current_controller = self.controllers[0]
        elif board.player_to_move == self.player_two_color:
            current_controller = self.controllers[1]

        return current_controller

    @staticmethod
    def _starting_infostates(arbiter_board: Board):
        blue_infostate = Infostate.at_start(owner=Player.BLUE,
                                            board=arbiter_board)
        red_infostate = Infostate.at_start(owner=Player.RED,
                                           board=arbiter_board)

        return blue_infostate, red_infostate

    def manage_pov_switching(self, arbiter_board: Board):
        """
        This is for setting the POV when one of the controllers is human.
        """
        # Assume that only one of the controllers is human
        if (self.get_current_controller(arbiter_board) == Controller.HUMAN
                and arbiter_board.player_to_move == Player.BLUE):
            self.pov = POV.BLUE
        elif (self.get_current_controller(arbiter_board) == Controller.HUMAN
                and arbiter_board.player_to_move == Player.RED):
            self.pov = POV.RED
        elif Controller.HUMAN in self.controllers:
            self.pov = None

    def get_controller_input(self, arbiter_board: Board):
        """
        This is for obtaining the controller's chosen action, be it human or
        bot.
        """
        valid_actions = arbiter_board.actions()
        if self.get_current_controller(arbiter_board) == Controller.RANDOM:
            action = random.choice(valid_actions)
        elif self.get_current_controller(arbiter_board) == Controller.HUMAN:
            while action not in valid_actions:
                action = input("Choose a move: ")

        return action

    @staticmethod
    def _update_infostates(blue_infostate: Infostate, red_infostate: Infostate,
                           action: str, result: str):
        blue_infostate = blue_infostate.transition(action, result=result)
        red_infostate = red_infostate.transition(action, result=result)

        return blue_infostate, red_infostate

    def start(self):
        """
        This method simulates a GG match in the terminal, either taking input
        from humans or choosing moves based on an algorithm or even both.
        """
        arbiter_board = Board(self.setup_arbiter_matrix(),
                              player_to_move=Player.BLUE,
                              blue_anticipating=False, red_anticipating=False)
        if self.save_data:
            self.game_history.append(arbiter_board.matrix)

        blue_infostate, red_infostate = MatchSimulator._starting_infostates(
            arbiter_board)

        turn_number = 1
        branches_encountered = 0
        while not arbiter_board.is_terminal():
            self.manage_pov_switching(arbiter_board)

            MatchSimulator._print_game_status(turn_number, arbiter_board,
                                              infostates=[
                                                  blue_infostate,
                                                  red_infostate],
                                              pov=self.pov)
            valid_actions = arbiter_board.actions()
            branches_encountered += len(valid_actions)

            action = ""  # Initialize variable for storing chosen action
            action = self.get_controller_input(arbiter_board)
            print(f"Chosen Move: {action}")

            if self.save_data:
                self.game_history.append(action)

            new_arbiter_board = arbiter_board.transition(action)
            result = arbiter_board.classify_action_result(action,
                                                          new_arbiter_board)
            blue_infostate, red_infostate = MatchSimulator._update_infostates(
                blue_infostate, red_infostate, action=action, result=result
            )
            arbiter_board = new_arbiter_board
            turn_number += 1
