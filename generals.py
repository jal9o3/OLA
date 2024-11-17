import logging, copy, random

# Configure the logging
logging.basicConfig(level=logging.WARNING)

# Global constants
from world_constants import *

# Determine if the current state is a terminal state
def is_terminal(board, annotation):

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # If either of the flags have been captured
    if not any(FLAG in _ for _ in board) or \
       not any(SPY + FLAG in _ for _ in board):
        return True
    
    # If the blue flag is on the other side of the board
    if FLAG in board[-1]:
        # If flag has already survived a turn
        if annotation[WAITING_BLUE_FLAG]:
            return True
        else:
            flag_col = board[-1].index(FLAG) # Get the flag's column number
            return has_none_adjacent(flag_col, board[-1])

    # Do the same checking for the red flag
    if SPY + FLAG in board[0]:
        if annotation[WAITING_RED_FLAG]:
            return True
        else:
            flag_col = board[0].index(SPY + FLAG)
            return has_none_adjacent(flag_col, board[0])

    # If none of the checks have been passed, it is not a terminal state
    return False

# Obtain all possible actions for each state
def actions(board, annotation):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    current_player = annotation[CURRENT_PLAYER]
    # Set ranges of piece designations
    range_start, range_end = (
        (FLAG, SPY) if current_player == BLUE else (SPY + FLAG, SPY + SPY)
    )   

    def is_valid(square):
        return not (range_start <= square <= range_end) or square == BLANK

    moves = []
    # Iterate over every square of the board
    for row in range(ROWS):
        for column in range(COLUMNS):
            square = board[row][column]
            # Check for a piece that belongs to the current player
            if square <= range_end and square >= range_start:
                # Check for allied pieces in adjacent squares:
                if row != ROWS - 1: # UP
                    if is_valid(board[row + 1][column]):
                        moves.append(f"{row}{column}{row + 1}{column}")
                if row != 0: # DOWN
                    if is_valid(board[row - 1][column]):
                        moves.append(f"{row}{column}{row - 1}{column}")
                if column != COLUMNS - 1: # RIGHT
                    if is_valid(board[row][column + 1]):
                        moves.append(f"{row}{column}{row}{column + 1}")
                if column != 0: # LEFT
                    if is_valid(board[row][column - 1]):
                        moves.append(f"{row}{column}{row}{column - 1}")
    return moves            

def transition(board, annotation, action):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)

    def move_piece(start_row, start_col, end_row, end_col):
       new_board[end_row][end_col] = board[start_row][start_col]
       new_board[start_row][start_col] = BLANK

    def handle_challenges(challenger_value, target_value):
        # Edge case where PRIVATE defeats SPY
        if ((challenger_value == SPY and target_value == PRIVATE)
            or (challenger_value == PRIVATE and target_value == SPY)):
            move_piece(start_row, start_col, end_row, end_col)
            return
        # Stronger piece or flag challenge
        if (challenger_value > target_value
            or (challenger_value == FLAG and target_value == FLAG)):            
            move_piece(start_row, start_col, end_row, end_col)
        elif challenger_value < target_value:
            new_board[start_row][start_col] = BLANK # remove losing attacker
        else:
            # Remove both in tie
            new_board[start_row][start_col] = BLANK
            new_board[end_row][end_col] = BLANK
    
    new_board, new_annotation = copy.deepcopy(board), copy.deepcopy(annotation)

    # Obtain indices of starting and destination squares
    start_row, start_col, end_row, end_col = map(int, action)

    current_player = annotation[CURRENT_PLAYER]
    range_start = FLAG if current_player == BLUE else FLAG + SPY
    range_end = SPY if current_player == BLUE else SPY + SPY

    # Check if starting square's piece belongs to current player
    if not (board[start_row][start_col] != BLANK
            and range_start <= board[start_row][start_col] <= range_end):
        return None
    
    # Check if destination square's piece does not belong to the current player
    if (board[end_row][end_col] != BLANK
        and range_start <= board[end_row][end_col] <= range_end):
        return None

    # If the destination square is blank, move selected piece to it
    if board[end_row][end_col] == BLANK:
        move_piece(start_row, start_col, end_row, end_col)
    elif current_player == BLUE: # Handle challenges
        opponent_value = board[end_row][end_col] - SPY
        handle_challenges(board[start_row][start_col], opponent_value)
    elif current_player == RED:
        own_value = board[start_row][start_col] - SPY
        handle_challenges(own_value, board[end_row][end_col])
        
    new_annotation[CURRENT_PLAYER] = RED if current_player == BLUE else BLUE
    # If the blue flag reaches the other side
    if (FLAG in board[-1] and not annotation[WAITING_BLUE_FLAG]
        and not has_none_adjacent(board[-1].index(FLAG), board[-1])):
        new_annotation[WAITING_BLUE_FLAG] = 1
    # Check for the red flag
    elif (SPY + FLAG in board[0] and not annotation[WAITING_RED_FLAG]
          and not has_none_adjacent(board[0].index(SPY + FLAG), board[0])):
        new_annotation[WAITING_RED_FLAG] = 1
    return (new_board, new_annotation)          

# Procedure for checking adjacent enemy pieces in waiting flags
def has_none_adjacent(flag_col, nrow): # nrow is either the first or last row
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # If not at the left or rightmost edge of the board
    if flag_col != 0 and flag_col != COLUMNS - 1:
        # Check both squares to the left and right
        if not nrow[flag_col - 1] and not nrow[flag_col + 1]:
            return True
    elif flag_col == 0 and not nrow[flag_col + 1]:
        # If flag is at the first column and the square next to it is empty
        return True
    elif flag_col == COLUMNS - 1 and not nrow[flag_col - 1]:
        # If flag is at the last column and the square before it is empty
        return True
    else:
        return False

def print_matrix(board, color=False, pov=WORLD):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    def colored(text, color_code):
        return f"\033[{color_code}m{text:2}\033[0m"
    
    print()
    for i, row in enumerate(board):
        print(f"{i:2}", end='  ')
        for j, elem in enumerate(row): 
            if elem == BLANK:
                print(" -", end=' ')
            elif pov == WORLD:
                if color and elem == FLAG:
                    print(colored(elem, "34"), end=' ')  # Blue
                elif color and elem == FLAG + SPY:
                    print(colored(elem, "31"), end=' ')  # Red
                elif elem < 0:  # For board diffs
                    print(colored(abs(elem), "33"), end=' ')  # Yellow
                else:
                    print(f"{elem:2}", end=' ')
            elif pov in {BLIND, BLUE, RED}:
                is_blue_pov = pov in {BLIND, BLUE}
                if elem <= SPY and elem >= FLAG:
                    if color and elem == FLAG and is_blue_pov:
                        print(colored(elem, "34"), end=' ')  # Blue
                    elif color and elem == FLAG + SPY and not is_blue_pov:
                        print(colored(elem, "31"), end=' ')  # Red
                    else:
                        print(f"{elem:2}", end=' ')
                else:
                    unknown = BLUE_UNKNOWN if is_blue_pov else RED_UNKNOWN
                    print(f"{unknown:2}", end=' ')                    
        print()
    print("\n    ", end='')
    for k in range(COLUMNS):
        print(f"{k:2}", end=' ')
    print()       

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)

    # Board for arbiter
    board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    annotation = [BLUE, 0, 0]
    
    # Boards for both player POVs
    blue_board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    red_board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    
    # Initial formations span three rows
    blue_formation = [BLANK for _ in range(COLUMNS) for _ in range(3)]
    red_formation = [BLANK for _ in range(COLUMNS) for _ in range(3)]

    # formation_temp = input("BLUE formation: ")
    formation_temp = "0 15 15 2 2 2 2 0 2 3 4 5 6 7 8 9 10 11 0 13 14 0 0 12 2 0 1"
    # Preprocess input
    for i, p in enumerate(formation_temp.split(" ")):
        blue_formation[i] = int(p)

    # Place pieces on blue board
    i = 0
    for row in range(ROWS-3, ROWS):
        for column in range(COLUMNS):
            if i < len(blue_formation):
                blue_board[row][column] = blue_formation[i]
                i += 1

    # Flip the blue board matrix: Flip the blue board matrix upside down
    blue_board = blue_board[::-1]
    # Flip each blue board row left to right
    blue_board = [row[::-1] for row in blue_board]

    # formation_temp = input("RED formation: ")
    formation_temp = "0 15 0 2 2 2 2 2 2 3 4 5 6 7 0 9 10 11 12 13 14 0 0 8 15 0 1"
    # Preprocess input
    for i, p in enumerate(formation_temp.split(" ")):
        if int(p) != BLANK:
            red_formation[i] = int(p) + SPY # Red pieces range from 15 to 30

    # Place pieces on red board
    i = 0
    for row in range(ROWS-3, ROWS):
        for column in range(COLUMNS):
            if i < len(red_formation):
                red_board[row][column] = red_formation[i]
                i += 1

    # Perform matrix addition
    board = [[blue_board[i][j] + red_board[i][j] for j in range(COLUMNS)] for i in range(len(board))]


    # Flip the board matrix for the standard POV (blue on the bottom side):
    standard_pov = board[::-1]
    #standard_pov = [row[::-1] for row in standard_pov] # flip rows

    # Gameplay loop
    mode = RANDOM_VS_RANDOM
    i = 0
    moves_N = 0 # total number of branches found
    if mode == HUMAN_VS_RANDOM:
        human = random.choice([BLUE, RED])
        print(f"You are player {human}")
    else:
        human = 0
    while not is_terminal(board, annotation):
        print(f"\nTurn: {i + 1}")
        if mode == RANDOM_VS_RANDOM:
            print_matrix(board, color=True, pov=WORLD)
        elif mode == HUMAN_VS_RANDOM:
            print_matrix(board, color=True, pov=human)
        print(f"Player: {annotation[CURRENT_PLAYER]}")
        moves = actions(board, annotation)
        print(moves)
        moves_N += len(moves)
        print(f"Possible Moves: {len(moves)}")
        move = ""
        if mode == HUMAN_VS_RANDOM and annotation[CURRENT_PLAYER] == human:
            while move not in moves:
                move = input("Move: ")
        else:
            move = random.choice(moves)
        print(f"Chosen Move: {move}")

        # Examine move result (WIN, LOSS, TIE):
        new_board, new_annotation = transition(board, annotation, move)
        # Perform matrix subtraction on old and new boards
        board_diff = [[board[i][j] - new_board[i][j] for j in range(len(board[0]))] for i in range(len(board))]

        print("Board Diff:")
        print_matrix(board_diff)
        # Overwrite old state
        board, annotation = new_board, new_annotation
        
        i += 1
    print(f"Average branching: {round(moves_N/i)}")
    
if __name__ == "__main__":
    main()
