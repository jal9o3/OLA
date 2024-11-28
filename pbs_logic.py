import logging, random

logging.basicConfig(level=logging.WARNING)

# World constants
from world_constants import *

# Public belief state constants
from pbs_constants import *

def public_observation(public_belief_state, pbs_annotation, action, result):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    start_row, start_col, end_row, end_col = map(int, action)

    # Determine which piece to update "surpasses" count (attacker or defender)
    for i, piece in enumerate(public_belief_state):
        if (piece[PBS_ROW] == start_row and piece[PBS_COLUMN] == start_col
            or piece[PBS_ROW] == end_row and piece[PBS_COLUMN] == end_col
            and piece[PBS_CAPTURED] == 0):
            piece_to_update = i # current piece
    
    # Restart loop to identify the other piece
    for i, piece in enumerate(public_belief_state):
        if (public_belief_state[piece_to_update][PBS_ROW] == start_row
            and public_belief_state[piece_to_update][PBS_COLUMN] == start_col):
            if (piece[PBS_ROW] == end_row and piece[PBS_COLUMN] == end_col
                and piece[PBS_CAPTURED] == 0):
                logger.debug(f"found other piece end square {i}")
                other_piece = i
        elif (public_belief_state[piece_to_update][PBS_ROW] == end_row
                and public_belief_state[piece_to_update][PBS_COLUMN] == end_col
                and piece[PBS_CAPTURED == 0]):
            if (piece[PBS_ROW] == start_row and piece[PBS_COLUMN] == start_col):
                logger.debug(f"found other piece start square {i}")
                other_piece = i
    
    # Update the "surpasses" count based on the action result
    # Distinguish whether piece to update is the attacker or defender
    if (result != OCCUPY
        and public_belief_state[piece_to_update][PBS_ROW] == start_row
        and public_belief_state[piece_to_update][PBS_COLUMN] == start_col):
        is_attacker = True
    else:
        is_attacker = False

    # Perform the update
    if result == DRAW:
        public_belief_state[piece_to_update][PBS_KILL_COUNT] += 1
        public_belief_state[other_piece][PBS_KILL_COUNT] += 1
    elif result == WIN:
        # Update as attacker or defender
        if is_attacker:
            public_belief_state[piece_to_update][PBS_KILL_COUNT] += 1
        else:
            public_belief_state[other_piece][PBS_KILL_COUNT] += 1
    # No necessary update for occupation
    elif result == LOSS:
        if is_attacker:
            public_belief_state[other_piece][PBS_KILL_COUNT] += 1
        else:
            public_belief_state[piece_to_update][PBS_KILL_COUNT] += 1

     # Update piece locations
    def handle_draw_update(piece):
        if piece[PBS_PLAYER] == BLUE:
            piece[PBS_ROW] = -1
            piece[PBS_COLUMN] = -1 # Send piece outside the board
        else:
            piece[PBS_ROW] = ROWS + 1
            piece[PBS_COLUMN] = COLUMNS + 1
        piece[PBS_CAPTURED] = 1

    for i, piece in enumerate(public_belief_state):
        if (piece[PBS_ROW] == start_row
            and piece[PBS_COLUMN] == start_col):
            # Draw
            if result == DRAW:
                handle_draw_update(piece)
            # Successful attacker or occupant or loss
            # Denotes either relocation or location of successful defender
            elif result == WIN or result == OCCUPY or result == LOSS:
                piece[PBS_ROW] = end_row
                piece[PBS_COLUMN] = end_col
                if result == LOSS and piece[PBS_PLAYER] == pbs_annotation[CURRENT_PLAYER]:
                    piece[PBS_CAPTURED] = 1

    for i, piece in enumerate(public_belief_state):
        if (piece[PBS_ROW] == end_row
            and piece[PBS_COLUMN] == end_col):
            if result == DRAW:
                handle_draw_update(piece)
            elif result == WIN and piece[PBS_PLAYER] != pbs_annotation[CURRENT_PLAYER]:
                piece[PBS_CAPTURED] = 1
            # No defender in occupation
            # No location update for winning defender
    
    pbs_annotation[CURRENT_PLAYER] = RED if pbs_annotation[CURRENT_PLAYER] == BLUE else BLUE

    return public_belief_state, pbs_annotation

def print_pbs(pbs, annotation):
    # For side by side display of top and bottom half of PBS
    split_pbs = [
        pbs[:INITIAL_ARMY], 
        pbs[INITIAL_ARMY:2*INITIAL_ARMY]
        ]
    def print_row_half(half_index, i, j):
        print(f"{round(split_pbs[half_index][i][j]):2}", end=' ')

    print("\nPBS: BLUE Pieces - RED Pieces")
    print("Columns: Player-x-y-kills-is_captured")

    for i in range(INITIAL_ARMY):
        for j in range(PBS_COLS):
            # Print row of first half
            print_row_half(0, i, j)
        print("  ", end='')
        for j in range(PBS_COLS):
            # Print row of second half
            print_row_half(1, i, j)
        # print piece numbers
        print(f"   {i}+{i+INITIAL_ARMY}", end=" ")
        print()