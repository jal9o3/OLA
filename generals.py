import logging, copy, random

# Set up basic configuration
logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# Create a logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.WARNING)

# Global constants for Game of the Generals
ROWS = 8
COLUMNS = 9

# Power Rankings of Pieces
BLANK = 0 # Unoccupied Square
FLAG = 1 # Philippine Flag
PRIVATE = 2 # One Chevron
SERGEANT = 3 # Three Chevrons
SECOND_LIEUTENANT = 4 # One Magdalo Triangle
FIRST_LIEUTENANT = 5 # Two Magdalo Triangles
CAPTAIN = 6 # Three Magdalo Triangles
MAJOR = 7 # One Magdalo Seven-Ray Sun
LIEUTENANT_COLONEL = 8 # Two Magdalo Seven-Ray Suns
COLONEL = 9 # Three Magdalo Seven-Ray Suns
BRIGADIER_GENERAL = 10 # One Star
MAJOR_GENERAL = 11 # Two Stars
LIEUTENANT_GENERAL = 12 # Three Stars
GENERAL = 13 # Four Stars
GENERAL_OF_THE_ARMY = 14 # Five Stars
SPY = 15 # Two Prying Eyes
# Red pieces will be denoted 16 (FLAG) to 30 (SPY)
UNKNOWN = 31 # Placeholder for unidentified enemy pieces

# Designations of players
BLUE = 1 # Moves first
RED = 2

# Designations of the annotation indices
CURRENT_PLAYER = 0
WAITING_BLUE_FLAG = 1 # If blue flag reaches enemy base with an adjacent enemy
WAITING_RED_FLAG = 2 # Same for the red flag

def main():
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
    formation_temp = "1 15 15 2 2 2 2 0 2 3 4 5 6 7 8 9 10 11 0 13 14 0 0 12 2 0 0"
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

    #print_matrix(blue_board)

    # formation_temp = input("RED formation: ")
    formation_temp = "1 15 0 2 2 2 2 2 2 3 4 5 6 7 0 9 10 11 12 13 14 0 0 8 15 0 0"
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

    #print_matrix(red_board)

    # Perform matrix addition
    board = [[blue_board[i][j] + red_board[i][j] for j in range(COLUMNS)] for i in range(len(board))]


    # Flip the board matrix for the standard POV (blue on the bottom side):
    standard_pov = board[::-1]
    #standard_pov = [row[::-1] for row in standard_pov] # flip rows

    # Sample random game ten plies deep
    for i in range(15):
        print(f"\nTurn: {i + 1}")
        print_matrix(board)
        print(f"Player: {annotation[CURRENT_PLAYER]}")
        move = random.choice(actions(board, annotation))
        print(f"Move: {move}")
        board, annotation = transition(board, annotation, move)

    
    #print_matrix(board)
    #print(f"Player: {annotation[CURRENT_PLAYER]}")

    #print_matrix(standard_pov)

    #print(is_terminal(board, annotation))

    #moves = actions(board, annotation)
    #print(moves)
    #xcprint(len(moves))

    #annotation[CURRENT_PLAYER] = RED

    #moves = actions(board, annotation)
    #print(moves)
    #print(len(moves))
    #new_board, new_annotation = transition(board, annotation, "0201")
    #print(f"Player: {new_annotation[CURRENT_PLAYER]}")

    #print_matrix(new_board)

# Determine if the current state is a terminal state
def is_terminal(board, annotation):
    # If either of the flags have been captured
    if not any(FLAG in _ for _ in board) or \
       not any(SPY + FLAG in _ for _ in board):
        logger.debug("Check #1")
        return True

    # Procedure for checking adjacent enemy pieces in waiting flags
    def has_adjacent(flag_col, nrow): # nrow is either the first or last row
        logger.debug(f"flag_col: {flag_col}")
        logger.debug("Inside has_adjacent function")
        # If not at the left or rightmost edge of the board
        if flag_col != 0 and flag_col != COLUMNS - 1:
            # Check both squares to the left and right
            if not nrow[flag_col - 1] and not nrow[flag_col + 1]:
                logger.debug("Not at edge, return True")
                return True
        elif flag_col == 0 and not nrow[flag_col + 1]:
            # If flag is at the first column and the square next to it is empty
            logger.debug("First column, return True")
            return True
        elif flag_col == COLUMNS - 1 and not nrow[flag_col - 1]:
            # If flag is at the last column and the square before it is empty
            logger.debug("Last column, return True")
            return True
        else:
            logger.debug("has_adjacent checks ended, return False")
            return False
    
    # If the blue flag is on the other side of the board
    if FLAG in board[-1]:
        # If flag has already survived a turn
        if annotation[WAITING_BLUE_FLAG]:
            logger.debug("Waiting blue flag, return True")
            return True
        else:
            flag_col = board[-1].index(FLAG) # Get the flag's column number
            return has_adjacent(flag_col, board[-1])

    # Do the same checking for the red flag
    if SPY + FLAG in board[0]:
        if annotation[WAITING_RED_FLAG]:
            logger.debug("Waiting red flag, return True")
            return True
        else:
            flag_col = board[0].index(SPY + FLAG)
            return has_adjacent(flag_col, board[0])

    # If none of the checks have been passed, it is not a terminal state
    logger.debug("No checks passed, return False")
    return False

# Obtain all possible actions for each state
def actions(board, annotation):
    current_player = annotation[CURRENT_PLAYER]
    logger.debug(f"Current Player: {current_player}")

    # Set ranges of piece designations
    if current_player == BLUE:
        range_start = FLAG
        range_end = SPY
    else:
        range_start = SPY + FLAG
        range_end = SPY + SPY
        
    moves = []
    # Iterate over every square of the board
    for row in range(ROWS):
        for column in range(COLUMNS):
            square = board[row][column]
            # Check for a piece that belongs to the current player
            if square <= range_end and square >= range_start:
                # Check for allied pieces in adjacent squares:
                if row != ROWS - 1: # UP
                    up_square = board[row + 1][column]
                    logger.debug(f"up: {up_square}")
                    if not up_square <= range_end and \
                       not up_square >= range_start or up_square == BLANK:
                        logger.debug("Appending up square")
                        moves.append(f"{row}{column}{row + 1}{column}")
                if row != 0: # DOWN
                    down_square = board[row - 1][column]
                    logger.debug(f"down {down_square}")
                    if not down_square <= range_end and \
                       not down_square >= range_start or down_square == BLANK:
                        logger.debug("Appending down square")
                        moves.append(f"{row}{column}{row - 1}{column}")
                if column != COLUMNS - 1: # RIGHT
                    right_square = board[row][column + 1]
                    logger.debug(f"right {right_square}")
                    if not right_square <= range_end and \
                       not right_square >= range_start or right_square == BLANK:
                        logger.debug("Appending right square")
                        moves.append(f"{row}{column}{row}{column + 1}")
                if column != 0: # LEFT
                    left_square = board[row][column - 1]
                    logger.debug(f"left {left_square}")
                    if not left_square <= range_end and \
                       not left_square >= range_start or left_square == BLANK:
                        logger.debug("Appending left square")
                        moves.append(f"{row}{column}{row}{column - 1}")
    return moves            

def transition(board, annotation, action):
    new_board = copy.deepcopy(board)
    new_annotation = copy.deepcopy(annotation)

    # Obtain indices of starting and destination squares
    start_row = int(action[0])
    start_col = int(action[1])
    end_row = int(action[2])
    end_col = int(action[3])

    current_player = annotation[CURRENT_PLAYER]
    
    range_start = FLAG if current_player == BLUE else FLAG + SPY
    range_end = SPY if current_player == BLUE else SPY + SPY

    # Check if starting square's piece belongs to current player
    if not (board[start_row][start_col] != BLANK and \
            board[start_row][start_col] <= range_end and \
            board[start_row][start_col] >= range_start):
        return None
    
    # Check if destination square's piece does not belong to the current player
    if board[end_row][end_col] != BLANK and \
       board[end_row][end_col] <= range_end and \
       board[end_row][end_col] >= range_start:
        return None

    def move_piece(start_row, start_col, end_row, end_col):
       new_board[end_row][end_col] = board[start_row][start_col]
       new_board[start_row][start_col] = BLANK

    def handle_challenges(challenger_value, target_value):
       # If challenging piece is stronger, move it to the opponent's square
       if challenger_value > target_value:
           move_piece(start_row, start_col, end_row, end_col)
       elif challenger_value < target_value:
           new_board[start_row][start_col] = BLANK # remove losing attacker
       elif challenger_value == target_value:
           new_board[start_row][start_col] = BLANK
           new_board[end_row][end_col] = BLANK # remove both in tie

    # If the destination square is blank, move selected piece to it
    if board[end_row][end_col] == BLANK:
        move_piece(start_row, start_col, end_row, end_col)
    elif current_player == BLUE: # Handle challenges
        opponent_value = board[end_row][end_col] - SPY
        handle_challenges(board[start_row][start_row], opponent_value)  
    elif current_player == RED:
        own_value = board[start_row][start_col] - SPY
        handle_challenges(own_value, board[end_row][end_col])
        
    new_annotation[CURRENT_PLAYER] = RED if current_player == BLUE else BLUE 
    return (new_board, new_annotation)          

def print_matrix(board):
    print()
    for i, row in enumerate(board):
        print(f"{i:2}", end='  ')
        for j, elem in enumerate(row): 
            print(f"{elem:2}", end=' ')
        print()
    print()
    print("    ", end='')
    for k in range(COLUMNS):
        print(f"{k:2}", end=' ')
    print()       

if __name__ == "__main__":
    main()
