import logging, math, itertools, random

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

PIECES = [1, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15]
# The number of unique permutations of the above pieces
# VALUE_PERMUTATIONS_N = (math.factorial(21))/math.factorial(6)*math.factorial(2)

# SAMPLE_N = ((1.96**2)*0.5*(1 - 0.5))/0.05**2
# Representative sample size
# ADJUSTED_SAMPLE_N = SAMPLE_N/(1 + ((SAMPLE_N - 1)/VALUE_PERMUTATIONS_N))

# Permutation generator
VALUE_PERMUTATIONS_GENERATOR = itertools.permutations(PIECES)

# TODO: define the usage of bayes theorem
def bayes_theorem(hypothesis, evidence):
    # p(H|E) =
    # p(E|H)*p(H)/p(E)
    """
    Hypothesis takes the form [i, r] where i is the index of the piece under
    assessment, and r is the rank in question. Evidence is defined as an array
    of size INITIAL_ARMY (21), of which each element j has the form [f, c],
    where f is the lowest possible value for the piece j, and c is the highest
    possible value.
    """

    # TODO: estimate p(E|H)
    # TODO: slice unique permutations
    value_permutations_slice = set(
        itertools.islice(VALUE_PERMUTATIONS_GENERATOR, 1000)
        ) # Representative sample size as ADJUSTED_SAMPLE_N
    

def private_observation(infostate, infostate_annotation, action, result):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    
    start_row, start_col, end_row, end_col = map(int, action)

    # Determine which piece to update range (attacker or defender)
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

    # Update the range of the piece based on the action result
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

    # TODO: Update the probabilities of piece identities
    # TODO: Accumulate all gathered relevant evidence
    # TODO: Use conditional probability to calculate the likelihoods

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

def main():
    def get_random_permutation(pieces):
        permuted_list = pieces[:]
        random.shuffle(permuted_list)
        return tuple(permuted_list)
    seen = set()
    for i in range(1000):
        permutation = get_random_permutation(PIECES)
        while permutation in seen:
            permutation = get_random_permutation(PIECES)
        seen.add(permutation)

    for permutation in seen:
        print(permutation)
                               

if __name__ == "__main__":
    main()