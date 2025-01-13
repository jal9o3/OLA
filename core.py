import random, logging

def get_random_permutation(elements: list):
    list_to_shuffle = elements[:]
    random.shuffle(list_to_shuffle)
    shuffled_list = list_to_shuffle
    return tuple(shuffled_list)

def get_blank_matrix(rows: int, columns:int):
    return [[Ranking.BLANK for col in range(columns)] for row in range(rows)]

class Player:
    def __init__(self, color: int):
        self.color = color
    
    def get_random_formation(piece_list: list[int]):
        return get_random_permutation(piece_list)

class Ranking:
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
    ROWS = 8
    COLUMNS = 9

    BLUE_PLAYER = 1
    RED_PLAYER = 2

    """
    The matrix is simply a representation of the current piece positions and
    ranks, with the rank designations being 0 to 30 (see constant definitions 
    in the Ranking class).

    blue_anticipating is True when the blue player's flag has reached the eighth
    row, but can still be challenged in the next turn by a red piece. If red 
    fails to challenge, blue wins. The same logic applies to red_anticipating,
    except that the red player's flag must reach the first row.
    """
    def __init__(self, matrix: list[list[int]], player_to_move: int, 
                 blue_anticipating: bool, red_anticipating: bool):
        self.matrix = matrix
        self.player_to_move = player_to_move
        self.blue_anticipating = blue_anticipating
        self.red_anticipating = red_anticipating
        
class MatchSimulator:
    """
    The mode parameter sets whether humans or algorithms choose the moves for
    either or both sides of the simulated match (see constant definitions 
    above).
    """
    # TODO: Define the mode designations
    def __init__(self, blue_formation: list[int], red_formation: list[int],
                 mode: int, save_data: bool):
        self.blue_formation = blue_formation
        self.red_formation = red_formation
        self.mode = mode
        self.save_data = save_data

    def _prepare_empty_matrices():
        arbiter_matrix = get_blank_matrix(rows=Board.ROWS, 
                                                columns=Board.COLUMNS)
        # TODO: set other arbiter board attributes (formerly annotation)
        blue_player_matrix = get_blank_matrix(rows=Board.ROWS, 
                                             columns=Board.COLUMNS)
        red_player_matrix = get_blank_matrix(rows=Board.ROWS, 
                                            columns=Board.COLUMNS)
        
        return arbiter_matrix, blue_player_matrix, red_player_matrix

    def _place_formation_on_matrix(formation: list[int], 
                                   matrix: list[list[int]]):
        # The formation is placed on the first three rows of the player's side
        # of the board. The formation list must enumerate from the furthermost
        # row (from the player's perspective) to the nearest, from left to 
        # right.
        i = 0
        for row in range(Board.ROWS-3, Board.ROWS):
            for column in range(Board.COLUMNS):
                if i < len(formation):
                    matrix[row][column] = formation[i]
                    i += 1
        
        return matrix
    
    def _flip_matrix(matrix: list[list[int]]):
        # Flip the matrix upside down
        matrix = matrix[::-1]
        # Flip each blue board row left to right
        matrix = [row[::-1] for row in matrix]

        return matrix
    
    def _combine_player_matrices(blue_player_matrix: list[list[int]],
                                 red_player_matrix: list[list[int]]):
        combined_matrix = [
            [blue_player_matrix[i][j] + red_player_matrix[i][j] for j in range(
                Board.COLUMNS)] for i in range(Board.ROWS)
        ]

        return combined_matrix

    def start(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        arbiter_matrix, blue_player_matrix, red_player_matrix = (
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
        

        



        
        


