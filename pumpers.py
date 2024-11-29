import json, os

# World constants
from world_constants import *

# Function for setting up PBSs
from generals import initial_pbs, transition, public_observation

# Procedure for saving a particular PBS
def pbs_pumper(game_tag, move_number, pbs_tag):
    # Load the game from history/game_tag.json
    with open(f'history/{game_tag}.json', 'r') as file:
        game_data = json.load(file)
    board = game_data[0]
    annotation = [BLUE, 0, 0]
    moves = game_data[1]

    # Setup initial PBS
    pbs, pbs_annotation = initial_pbs(board)

    # Iterate until the move number
    for i in range(move_number):
        move = moves[i]
        # Examine move result (WIN, LOSS, TIE):
        new_board, new_annotation = transition(board, annotation, move)
        # Perform matrix subtraction on old and new boards
        board_diff = [
            [board[i][j] - new_board[i][j] for j in range(len(board[0]))] 
            for i in range(len(board))
            ]

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
        
        # Update PBS
        pbs, pbs_annotation = public_observation(pbs, pbs_annotation, move, result)

        # Overwrite old state
        board, annotation = new_board, new_annotation

    # Save the produced PBS in pbs_samples/pbs_tag.json
    os.makedirs('pbs_samples', exist_ok=True)
    with open(f'pbs_samples/{pbs_tag}', 'w') as file:
        json.dump([pbs, pbs_annotation], file)

def infostate_pumper(game_tag, move_number, infostate_tag):
    pass