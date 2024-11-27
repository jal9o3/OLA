import logging, copy

logging.basicConfig(level=logging.WARNING)

# GLobal constants
from world_constants import *

INFOROWS = 42 # 21 pieces per player
INFOCOLS = 21 # see designations below

# Define information state columns
PLAYER = 0 # to which player a piece belongs
# 1 - 15 is the probability of being pieces 1 - 15
ROW = 16
COLUMN = 17 # Current location of the piece (if captured, location of capturer)
RANGE_BOT = 18 # Lowest possible value of a piece
RANGE_TOP = 19 # Highest possible value of a piece, these are equal once identified
CAPTURED = 20 # Whether the piece has been captured

# Annotation indices
# CURRENT_PLAYER = 0, like in the world state annotation
WAITING_FLAG = 1 # Corresponds to WAITING_BLUE or WAITING_RED flags in world
POV_PLAYER = 2 # to which the infostate belongs

def bayes_theorem(hypothesis, evidence):
    # p(H|E) =
    # p(E|H)*p(H)/p(E)
    pass

def conditional_probability(hypothesis, evidence):
    # p(H|E) =
    # p(H intersection E) / p(E)
    pass

def private_observation(infostate, infostate_annotation, action, result):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    start_row, start_col, end_row, end_col = map(int, action)

    logger.debug(f"Start:{start_row}{start_col}")
    logger.debug(f"End:{end_row}{end_col}")

    # TODO: determine which piece to update range (attacker or defender)
    for i, piece in enumerate(infostate):
        if ((piece[ROW] == int(start_row) and piece[COLUMN] == int(start_col) 
            or piece[ROW] == int(end_row) and piece[COLUMN] == int(end_col))
            and piece[CAPTURED] == 0
            ):
            if i < INITIAL_ARMY:
                piece_to_update = i # current piece
            # Get the identified piece
            elif i >= INITIAL_ARMY:
                # Get the value of the identified piece
                for j, value in enumerate(piece):
                    if 1 <= j <= 15 and value == 1:
                        identified_value = j
                        logger.debug(f"Piece i: {i}")
                        logger.debug(f"Identified value: {identified_value}")

    # TODO: update the range of the piece based on the action result
    # Distinguish whether piece to update is the attacker or defender
    if (result != OCCUPY
        and infostate[piece_to_update][ROW] == start_row 
        and infostate[piece_to_update][COLUMN] == start_col):
        is_attacker = True
    else:
        is_attacker = False

    if result == DRAW:
        # Perform the update
        infostate[piece_to_update][RANGE_BOT] = identified_value
        infostate[piece_to_update][RANGE_TOP] = identified_value
    elif result == WIN:
        # Update as attacker or defender
        if is_attacker: # Unidentified is greater than the known piece
            if identified_value + 1 <= SPY:
                infostate[piece_to_update][RANGE_BOT] = identified_value + 1
            else: # Edge case for when private beats spy
                infostate[piece_to_update][RANGE_BOT] = PRIVATE
                infostate[piece_to_update][RANGE_TOP] = PRIVATE
        else: # Unidentified is less than the known piece
            if identified_value != PRIVATE:
                infostate[piece_to_update][RANGE_TOP] = identified_value - 1
            else:
                infostate[piece_to_update][RANGE_TOP] = SPY
                infostate[piece_to_update][RANGE_BOT] = SPY
    # No necessary update for occupation
    elif result == LOSS:
        if is_attacker:
            if identified_value != PRIVATE:
                infostate[piece_to_update][RANGE_TOP] = identified_value - 1
            else:
                infostate[piece_to_update][RANGE_BOT] = SPY
                infostate[piece_to_update][RANGE_TOP] = SPY
        else:
            if identified_value + 1 <= SPY:
                infostate[piece_to_update][RANGE_BOT] = identified_value + 1
            else:
                infostate[piece_to_update][RANGE_BOT] = PRIVATE
                infostate[piece_to_update][RANGE_TOP] = PRIVATE

    def handle_draw_update(piece):
        if piece[PLAYER] == BLUE:
            piece[ROW] = -1
            piece[COLUMN] = -1 # Send piece outside the board
        else:
            piece[ROW] = ROWS + 1
            piece[COLUMN] = COLUMNS + 1
        piece[CAPTURED] = 1

    for i, piece in enumerate(infostate):
        if (piece[ROW] == int(start_row) 
            and piece[COLUMN] == int(start_col)):
            # Draw
            if result == DRAW:
                handle_draw_update(piece)
            # Successful attacker or occupant or loss
            # Denotes either relocation or location of successful defender
            elif result == WIN or result == OCCUPY or result == LOSS:
                piece[ROW] = int(end_row)
                piece[COLUMN] = int(end_col)
                if result == LOSS and piece[PLAYER] == infostate_annotation[CURRENT_PLAYER]:
                    piece[CAPTURED] = 1

    for i, piece in enumerate(infostate):
        if (piece[ROW] == int(end_row)
            and piece[COLUMN] == int(end_col)):
            if result == DRAW:
                handle_draw_update(piece)
            elif result == WIN and piece[PLAYER] != infostate_annotation[CURRENT_PLAYER]:
                piece[CAPTURED] = 1
            # No defender in occupation
            # No location update for winning defender

    infostate_annotation[CURRENT_PLAYER] = RED if infostate_annotation[CURRENT_PLAYER] == BLUE else BLUE 

    return infostate, infostate_annotation
            
def print_infostate(infostate, annotation):
    
    # For side by side display of top and bottom half of infostate
    split_infostate = [
        infostate[:INITIAL_ARMY], 
        infostate[INITIAL_ARMY:2*INITIAL_ARMY]
        ]
    
    def print_row_half(half_index, i, j):
        if abs(split_infostate[half_index][i][j]*100) < 100:
            print(f"{round(split_infostate[half_index][i][j]*100):2}", end=' ')
        else:
            print(f"{split_infostate[half_index][i][j]:2}", end=' ')

    print("\nInfostate: Opponent Pieces - Allied Pieces")
    print("Rows: Player-p(1:15)-x-y-floor-ceiling-is_captured")

    for i in range(INITIAL_ARMY):
        # print piece numbers
        print(f"{i}+{i+INITIAL_ARMY}", end=" ")
        for j in range(INFOCOLS):
            # TODO: print row of first half
            print_row_half(0, i, j)
        print("  ", end='')
        for j in range(INFOCOLS):
            # TODO: print row of second half
            print_row_half(1, i, j)
        print()
