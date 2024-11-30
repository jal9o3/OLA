import logging, copy, random, json, os

# Configure the logging
logging.basicConfig(level=logging.WARNING)

# World constants
from world_constants import *

# Infostate related functions
from infostate_logic import *

# Public belief state related functions
from pbs_logic import *



# Determine if the current state is a terminal state
def is_terminal(board, annotation):

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
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

# Measure overall reward of terminal states
# 1 is a blue win, -1 is a red win
def reward(board, annotation):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # A non-terminal state is not eligible of assessment
    if not is_terminal(board, annotation):
        logger.debug("state is not terminal")
        return None
    
    # Blue flag captured
    elif not any(FLAG in _ for _ in board):
        return -1
    
    # Red flag captured
    elif not any(SPY + FLAG in _ for _ in board):
        return 1

    # Blue flag reaches red side
    elif FLAG in board[-1]:
        logger.debug("blue flag in red side")
        # If flag has already survived a turn
        if annotation[WAITING_BLUE_FLAG]:
            return 1
        else:
            flag_col = board[-1].index(FLAG) # Get the flag's column number
            if has_none_adjacent(flag_col, board[-1]):
                return 1

    # Red flag reaches red side
    if SPY + FLAG in board[0]:
        if annotation[WAITING_RED_FLAG]:
            return -1
        else:
            flag_col = board[0].index(SPY + FLAG)
            if has_none_adjacent(flag_col, board[0]):
                return -1
    
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
    logger.setLevel(logging.DEBUG)

    def move_piece(start_row, start_col, end_row, end_col):
       new_board[end_row][end_col] = board[start_row][start_col]
       new_board[start_row][start_col] = BLANK

    def handle_challenges(challenger_value, target_value):
        # Edge case where PRIVATE defeats SPY
        if (challenger_value == PRIVATE and target_value == SPY):
            move_piece(start_row, start_col, end_row, end_col)
            return
        elif (challenger_value == SPY and target_value == PRIVATE):
            new_board[start_row][start_col] # remove losing attacker
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
    logger.setLevel(logging.DEBUG)

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

# Adapt counterfactual regret minimization to GG
def cfr(board, annotation, blue_probability, red_probability, 
        current_depth, max_depth):
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # logger.debug(f"Depth: {current_depth}")
    # logger.debug(f"Blue Probability: {blue_probability}")
    # logger.debug(f"Red Probability: {red_probability}")
    
    player = annotation[CURRENT_PLAYER]
    opponent = RED if player == BLUE else BLUE

    # Return payoff for 'terminal' states
    if current_depth == max_depth and is_terminal(board, annotation):
        logger.setLevel(logging.DEBUG)
        # logger.debug("terminal state!")
        # logger.debug(f"Reward: {-reward(board, annotation)}")
        return reward(board, annotation), []
    elif current_depth == max_depth and not is_terminal(board, annotation):
        return 0, [] # replace with neural network perhaps

    # Initialize strategy
    valid_actions = actions(board, annotation)
    actions_n = len(valid_actions)
    strategy = [1.0/actions_n for i in range(actions_n)] # Uniform strategy
    regret_sum = [0.0 for i in range(actions_n)]
    
    # Initialize action utilities
    util = [0.0 for i in range(actions_n)]
    # Initialize node utility
    node_util = 0

    # Iterate over children nodes and recursively call cfr
    for a, action in enumerate(valid_actions):
        next_board, next_annotation = transition(board, annotation, action)
        if player == BLUE:
            result = cfr(next_board, next_annotation, 
            red_probability * strategy[a], blue_probability,
            current_depth + 1, max_depth)
            # logger.debug(result)
            util[a] = -(result[0])
        else:
            result = cfr(next_board, next_annotation, 
            blue_probability, red_probability * strategy[a],
            current_depth + 1, max_depth)
            # logger.debug(result)
            util[a] = -(result[0])
        # Calculate node utility
        node_util += strategy[a] * util[a]
    
    # Calculate regret sum
    for a, action in enumerate(valid_actions):
        logger.setLevel(logging.DEBUG)
        regret = util[a] - node_util
        # logger.debug(f"Regret: {regret}")
        regret_sum[a] += (red_probability if player == BLUE else blue_probability) * regret
        # logger.debug(f"regret_sum[a]={regret_sum[a]}")

    # print("Regret Sum:")
    # print(regret_sum)

    # Normalize regret sum to find strategy for this node
    strategy = [0.0 for i in range(actions_n)]
    normalizing_sum = sum(regret_sum)
    # for a, action in enumerate(valid_actions):
    #     logger.debug(f"regret_sum[a]={regret_sum[a]}")
    #     normalizing_sum += regret_sum[a]

    # logger.setLevel(logging.DEBUG)
    # logger.debug(f"Normalizing Sum: {normalizing_sum}")
    # logger.debug(f"Normalizing Sum > 0: {normalizing_sum > 0}")

    for a, action in enumerate(valid_actions):
        if normalizing_sum > 0:
            strategy[a] = regret_sum[a] / normalizing_sum
        else:
            strategy[a] = 1.0 / actions_n

    # Return node utility
    return node_util, strategy


# Represent initial information states for BLUE and RED
# 42 ROWS (21 pieces each) by 19 COLS (Player, p(1...15), row, col, captured)
def initial_infostate(board, player):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    
    # Initialize blank matrix for the infostate
    infostate = [[BLANK for _ in range(INFOCOLS)] for _ in range(INFOROWS)]
    infostate_annotation = [BLUE, 0, player]

    range_start, range_end = (
        (FLAG, SPY) if player == BLUE else (FLAG + SPY, 2*SPY)
    )
    # Obtain initial probabilities
    range_offset = 0 if player == BLUE else SPY # for finding the correct columns
    for piece in range(INITIAL_ARMY):
        for col in range(INFOCOLS):
            if col == PLAYER:
                infostate[piece][col] = RED if player == BLUE else BLUE
            elif range_start - range_offset <= col <= range_end - range_offset:
                if col == PRIVATE:
                    infostate[piece][col] = 6/INITIAL_ARMY
                elif col == SPY:
                    infostate[piece][col] = 2/INITIAL_ARMY
                else:
                    infostate[piece][col] = 1/INITIAL_ARMY
    piece_n = 0
    # Add locations
    for row in range(ROWS):
        for column in range(COLUMNS):
            # Locations of opponent's pieces
            if (piece_n < INITIAL_ARMY and
                not (range_start <= board[row][column] <= range_end)
                and board[row][column] != BLANK):
                infostate[piece_n][ROW] = row
                infostate[piece_n][COLUMN] = column
                # Set initial value range (for evidence pruning)
                infostate[piece_n][RANGE_BOT] = FLAG
                infostate[piece_n][RANGE_TOP] = SPY
                piece_n += 1
    # Restart loop to obtain the player's piece locations
    for row in range(ROWS):
        for column in range(COLUMNS):
            if (piece_n >= INITIAL_ARMY and
                    range_start <= board[row][column] <= range_end
                    and board[row][column] != BLANK):
                value = (
                    board[row][column] if player == BLUE
                    else board[row][column] - SPY
                ) # calculate actual value of the piece
                logger.debug(f"{piece_n} {value}")
                infostate[piece_n][PLAYER] = player
                infostate[piece_n][value] = 1
                infostate[piece_n][ROW] = row
                infostate[piece_n][COLUMN] = column
                # Possible value range ends are equal for identified pieces
                infostate[piece_n][RANGE_BOT] = value
                infostate[piece_n][RANGE_TOP] = value
                piece_n += 1
    
    return infostate, infostate_annotation

# Represent initial public belief state
def initial_pbs(board):
    # Initialize blank matrix for the infostate
    pbs = [[BLANK for _ in range(PBS_COLS)] for _ in range(PBS_ROWS)]
    pbs_annotation = [BLUE]

    blue_range_start, blue_range_end = FLAG, SPY
    red_range_start, red_range_end = SPY + FLAG, 2*SPY

    piece_n = 0
    # Add locations
    for row in range(ROWS):
        for column in range(COLUMNS):
            # Locations of BLUE's pieces
            if (piece_n < INITIAL_ARMY and
                blue_range_start <= board[row][column] <= blue_range_end
                and board[row][column] != BLANK):
                pbs[piece_n][PBS_PLAYER] = BLUE
                pbs[piece_n][PBS_ROW] = row
                pbs[piece_n][PBS_COLUMN] = column
                piece_n += 1
    # Restart loop to obtain RED's piece locations
    for row in range(ROWS):
        for column in range(COLUMNS):
            if (piece_n >= INITIAL_ARMY and
                    red_range_start <= board[row][column] <= red_range_end
                    and board[row][column] != BLANK):
                pbs[piece_n][PBS_PLAYER] = RED
                pbs[piece_n][PBS_ROW] = row
                pbs[piece_n][PBS_COLUMN] = column
                piece_n += 1
    return pbs, pbs_annotation

def print_board(board, color=False, pov=WORLD):
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
                if elem <= SPY and elem >= FLAG and is_blue_pov: # if piece is blue and pov is blue
                    if color and elem == FLAG and is_blue_pov: # color flag according to pov
                        print(colored(elem, "34"), end=' ')  # Blue
                    else:
                        print(f"{elem:2}", end=' ')
                elif elem <= 2*SPY and elem >= FLAG + SPY and not is_blue_pov:
                    if color and elem == FLAG + SPY and not is_blue_pov:
                        print(colored(elem - SPY, "31"), end=' ')  # Red
                    else:
                        print(f"{elem - SPY:2}", end=' ')
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
    logger.setLevel(logging.DEBUG)

    # True if game data will be saved
    save_game = True

    # Board for arbiter
    board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    annotation = [BLUE, 0, 0]
    
    # Boards for both player POVs
    blue_board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    red_board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    
    # Initial formations span three rows
    blue_formation = [BLANK for _ in range(COLUMNS) for _ in range(3)]
    red_formation = [BLANK for _ in range(COLUMNS) for _ in range(3)]

    formation_components = [0, 0, 0, 0, 0, 0,
                            1, 2, 2, 2, 2, 2, 2,
                            3, 4, 5, 6, 7, 8, 9, 10, 
                            11, 12, 13, 14, 15, 15]

    # Sample random formation
    blue_formation = list(get_random_permutation(formation_components))
    red_formation = list(get_random_permutation(formation_components))

    # formation_temp = input("BLUE formation: ")
    # formation_temp = "0 15 15 2 2 2 2 0 2 3 4 5 6 7 8 9 10 11 0 13 14 0 0 12 2 0 1"
    # # Preprocess input
    # for i, p in enumerate(formation_temp.split(" ")):
    #     blue_formation[i] = int(p)

    # Place pieces on blue board
    i = 0
    for row in range(ROWS-3, ROWS):
        for column in range(COLUMNS):
            if i < len(blue_formation):
                blue_board[row][column] = blue_formation[i]
                i += 1

    # Flip the blue board matrix:
    # Flip the blue board matrix upside down
    blue_board = blue_board[::-1]
    # Flip each blue board row left to right
    blue_board = [row[::-1] for row in blue_board]

    # # formation_temp = input("RED formation: ")
    # formation_temp = "0 15 0 2 2 2 2 2 2 3 4 5 6 7 0 9 10 11 12 13 14 0 0 8 15 0 1"
    # # Preprocess input
    # for i, p in enumerate(formation_temp.split(" ")):
    #     if int(p) != BLANK:
    #         red_formation[i] = int(p) + SPY # Red pieces range from 15 to 30

    # Place pieces on red board
    i = 0
    for row in range(ROWS-3, ROWS):
        for column in range(COLUMNS):
            if i < len(red_formation):
                if red_formation[i] > 0:
                    red_board[row][column] = red_formation[i] + SPY # take note of this change!
                elif red_formation[i] == 0:
                    red_board[row][column] = red_formation[i]
                i += 1

    # Perform matrix addition
    board = [
        [blue_board[i][j] + red_board[i][j] for j in range(COLUMNS)] 
        for i in range(len(board))
        ]
    
    print_board(board, annotation)
    
    # Handle game saving
    if save_game:
        # Save the initial board configuration, initial annotation is always the same
        game_data = [board]
            
    blue_infostate, blue_infostate_annotation = initial_infostate(board, BLUE)
    red_infostate, red_infostate_annotation = initial_infostate(board, RED)
    
    pbs, pbs_annotation = initial_pbs(board)

    # Gameplay loop
    # mode = RANDOM_VS_RANDOM
    # mode = HUMAN_VS_RANDOM
    mode = CFR_VS_CFR
    i = 0
    moves_N = 0 # total number of branches found
    if mode == HUMAN_VS_RANDOM:
        human = random.choice([BLUE, RED])
        print(f"You are player {human}")
    else:
        human = 0

    if save_game:
        move_history = [] # Initialize list of moves

    while not is_terminal(board, annotation):
        print(f"\nTurn: {i + 1}")
        
        if mode == RANDOM_VS_RANDOM:
            print_board(board, color=True, pov=WORLD)
            # print_infostate(blue_infostate, blue_infostate_annotation)
            # print_infostate(red_infostate, red_infostate_annotation)
            print_pbs(pbs, pbs_annotation)
        elif mode == HUMAN_VS_RANDOM:
            print_board(board, color=True, pov=human)
            print_pbs(pbs, pbs_annotation)
        elif mode == CFR_VS_CFR:
            print_board(board, color=True, pov=WORLD)

        print(f"Player: {annotation[CURRENT_PLAYER]}")
        moves = actions(board, annotation)
        print(moves)
        moves_N += len(moves)
        print(f"Possible Moves: {len(moves)}")
        move = ""
        if mode == HUMAN_VS_RANDOM and annotation[CURRENT_PLAYER] == human:
            while move not in moves:
                move = input("Move: ")
        elif mode == RANDOM_VS_RANDOM:
            move = random.choice(moves)
        elif mode == CFR_VS_CFR:
            util, strategy = cfr(board, annotation, 1, 1, 0, 3)
            print("Strategy: ")
            print(strategy)
            logger.setLevel(logging.DEBUG)
            logger.debug(f"Len: {len(strategy)}")
            print(f"Utility: {util}")
            # Set negative weights to zero to avoid errors
            for a, action in enumerate(strategy):
                if action < 0:
                    strategy[a] = 0
            print("Sanitized Strategy: ")
            print(strategy)
            move = random.choices(moves, weights=strategy, k=1)[0]
        print(f"Chosen Move: {move}")

        # Handle the saving of game moves
        if save_game:
            move_history.append(move)

        # Examine move result (WIN, LOSS, TIE):
        new_board, new_annotation = transition(board, annotation, move)
        # Perform matrix subtraction on old and new boards
        board_diff = [[board[i][j] - new_board[i][j] for j in range(len(board[0]))] for i in range(len(board))]

        # Examine move result
        start_row, start_col, end_row, end_col = map(int, move) # get indices
        challenger, target = board[start_row][start_col], board[end_row][end_col]
        result = -1 # Placeholder value

        # If the challenge removed both challenger and target (DRAW)
        if (board_diff[start_row][start_col] == challenger
            and board_diff[end_row][end_col] == target):
            result = DRAW
        elif (board_diff[start_row][start_col] == challenger
              and board_diff[end_row][end_col] == (target - challenger)):
            if board[end_row][end_col] == BLANK:
                result = OCCUPY # if no piece has been displaced
            else:
                result = WIN
        elif (board_diff[start_row][start_col] == challenger
              and board_diff[end_row][end_col] == BLANK):
            result = LOSS
              
        results = ["DRAW", "WIN", "OCCUPY", "LOSS"]
        print(f"Result: {results[result]}")

        # Update infostate
        blue_infostate, blue_infostate_annotation = private_observation(
            blue_infostate, blue_infostate_annotation, move, result)
        red_infostate, red_infostate_annotation = private_observation(
            red_infostate, red_infostate_annotation, move, result
        )

        # Update PBS
        pbs, pbs_annotation = public_observation(pbs, pbs_annotation, move, result)
            
        # Overwrite old state
        board, annotation = new_board, new_annotation
        
        i += 1
    
    outcomes = ["DRAW", "BLUE", "RED"]
    print(f"Winner: {outcomes[reward(board, annotation)]}")

    # Handle saving of latest game to a JSON file
    if save_game:
        game_data.append(move_history)
        os.makedirs('history', exist_ok=True)
        with open('history/latest_game.json', 'w') as file:
            json.dump(game_data, file)
    print(f"Average branching: {round(moves_N/i)}")
    
if __name__ == "__main__":
    main()
