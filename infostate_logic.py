import logging, random, copy, itertools, time

logging.basicConfig(level=logging.WARNING)

# World constants
from world_constants import *

# Infostate constants
from infostate_constants import *

# Class for the 3D infostate
class Infostate3D:
    def __init__(self, owner, board, player_to_move, waiting_flag=False):
        self.owner = owner
        self.board = board
        self.player_to_move = player_to_move
        self.waiting_flag = waiting_flag
    
    def start(self, board, owner):
        obscured_board = copy.deepcopy(board)
        # Add value ranges for the pieces
        for i, row in enumerate(board):
            for j, square in enumerate(row):
                if owner == BLUE and (FLAG + SPY <= square <= SPY*2):
                    obscured_board[i][j] = [RED_UNKNOWN, FLAG, SPY]
                elif owner == BLUE and (FLAG <= square <= SPY):
                    obscured_board[i][j] = [board[i][j], board[i][j], board[i][j]]
                elif owner == RED and (FLAG <= square <= SPY):
                    obscured_board[i][j] = [BLUE_UNKNOWN, FLAG, SPY]
                elif owner == RED and (FLAG + SPY <= square <= SPY*2):
                    obscured_board[i][j] = [board[i][j], board[i][j], board[i][j]]
                elif square == BLANK:
                    obscured_board[i][j] = [BLANK, BLANK, BLANK] 
        starting_infostate = Infostate3D(owner, obscured_board, 
                                         player_to_move=BLUE)
        return starting_infostate
    
    def private_observation(old_infostate, action, result):
        start_row, start_col, end_row, end_col = map(int, action)

        # Determine which piece to update range (attacker or defender)
        # Check if attacker or defender is unknown

        # Update the range of the piece based on the action result

        new_infostate = Infostate3D()
        return new_infostate



def get_random_permutation(pieces):
        permuted_list = pieces[:]
        random.shuffle(permuted_list)
        return tuple(permuted_list)

# Sample n permutations from the set of unique value permutations
def value_permutation_sample(pieces, n):
    
    seen = set()
    for i in range(n):
        permutation = get_random_permutation(pieces)
        while permutation in seen:
            permutation = get_random_permutation(pieces)
        seen.add(permutation)
    
    return seen

def get_result(board, annotation, move, new_board, new_annotation):
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
            
    # results = ["DRAW", "WIN", "OCCUPY", "LOSS"]
    # print(f"Result: {results[result]}")

    return result

# Functions for the 2D infostate

# Define the usage of bayes theorem
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

    piece_to_assess, possible_value = hypothesis[0], hypothesis[1]
    sample_size = 1000

    # Estimate p(E|H)
    p_evidence = 0
    p_evidence_with_hypothesis = 0
    while p_evidence == 0: # avoid division by zero errors
        # Sample unique permutations
        sample = value_permutation_sample(PIECES, sample_size)
        for permutation in sample:
            # Estimate p(E)
            # Check if the current permutation matches the evidence
            is_match = True
            for piece, fact in enumerate(evidence):
                lower_bound, upper_bound = fact[0], fact[1]
                if lower_bound <= permutation[piece] <= upper_bound:
                    pass # Do nothing as long as the evidence is matched
                else:
                    is_match = False
                    break # Stop iterating over evidence once contradicted
            if is_match:
                p_evidence += 1 # Increase the probability of the evidence
                # Estimate p(E intersection H)
                # If the hypothesis is also true, increase p(E intersection H)
                if permutation[piece_to_assess] == possible_value:
                    p_evidence_with_hypothesis += 1
        
        # Scale probabilities in relation to the sample size
        p_evidence /= sample_size
        p_evidence_with_hypothesis /= sample_size

        # Obtain probability of hypothesis
        p_hypothesis = 0
        for piece in PIECES:
            if piece == possible_value:
                p_hypothesis += 1
        
        p_hypothesis /= sample_size

    # Recall: p(E|H) = p(E intersection H) / p(H)
    return p_evidence_with_hypothesis/p_evidence

# Create a board representation of the infostate
def infostate_board(infostate, infostate_annotation):
    # Instantitiate the empty board
    board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    
    # Iterate through rows of the infostate
    for piece in infostate:
    # If current row represents an uncaptured piece, add it to the board 
        if piece[CAPTURED] != 1:
            # Add SPY (15) if piece is red
            offset = SPY if piece[PLAYER] == RED else BLANK
            # Get the lowest possible value for the piece
            board[piece[ROW]][piece[COLUMN]] = piece[RANGE_BOT] + offset
    
    return board, [infostate_annotation[CURRENT_PLAYER], 0, 0]

def private_observation(old_infostate, old_infostate_annotation, action, result, update_probabilities=False):
    # start_time = time.time()
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Create a copy of the old infostate
    infostate, infostate_annotation = copy.deepcopy(old_infostate), copy.deepcopy(old_infostate_annotation)

    start_row, start_col, end_row, end_col = map(int, action)

    # Determine which piece to update range (attacker or defender)
    for i, piece in enumerate(infostate):
        # logger.setLevel(logging.DEBUG)
        # logger.debug(f"i: {i}")
        if ((piece[ROW] == start_row and piece[COLUMN] == start_col 
            or piece[ROW] == end_row and piece[COLUMN] == end_col)
            and piece[CAPTURED] == 0
            ):
            if i < INITIAL_ARMY:
                piece_to_update = i # current piece
            # Get the identified piece
            elif i >= INITIAL_ARMY:
                identified_value = piece[RANGE_BOT]

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
        if (piece[ROW] == start_row 
            and piece[COLUMN] == start_col):
            # Draw
            if result == DRAW:
                handle_draw_update(piece)
            # Successful attacker or occupant or loss
            # Denotes either relocation or location of successful defender
            elif result == WIN or result == OCCUPY or result == LOSS:
                piece[ROW] = end_row
                piece[COLUMN] = end_col
                if result == LOSS and piece[PLAYER] == infostate_annotation[CURRENT_PLAYER]:
                    piece[CAPTURED] = 1

    for i, piece in enumerate(infostate):
        if (piece[ROW] == end_row
            and piece[COLUMN] == end_col):
            if result == DRAW:
                handle_draw_update(piece)
            elif result == WIN and piece[PLAYER] != infostate_annotation[CURRENT_PLAYER]:
                piece[CAPTURED] = 1
            # No defender in occupation
            # No location update for winning defender

    # Update the probabilities of piece identities
    if result != OCCUPY and update_probabilities:
        # Accumulate all gathered relevant evidence
        evidence = []
        for i, piece in enumerate(infostate):
            if i == INITIAL_ARMY:
                break
            evidence.append([piece[RANGE_BOT], piece[RANGE_TOP]])

        # Use conditional probability to calculate the likelihoods
        for i, piece in enumerate(infostate):
            if i == INITIAL_ARMY:
                break
            for j, value in enumerate(piece):
                if 1 <= j <= 15:
                    hypothesis = [i, j]
                    piece[j] = bayes_theorem(hypothesis, evidence)

    infostate_annotation[CURRENT_PLAYER] = RED if infostate_annotation[CURRENT_PLAYER] == BLUE else BLUE 

    # end_time = time.time()
    # print(f"Runtime: {end_time - start_time} seconds")

    return infostate, infostate_annotation

def infostate_to_string(infostate, infostate_annotation):
    infostr = ""
    # for row in infostate:
    #     for item in row:
    #         infostr += " " + str(item)

    # Flatten the infostate
    flat_infostate = list(itertools.chain.from_iterable(infostate))
    
    # for item in infostate_annotation:
    #     infostr += " " + str(item)

    # Extra zeroes to complete the six columns
    # for i in range(3):
    #     infostr += " 0"

    # Combine the flat infostate and the infostate annotation into a string
    # Include a padding of three zeroes at the end of the string (might remove later)
    infostr = " ".join(
        map(str, flat_infostate)) + " " + " ".join(
            map(str, infostate_annotation)) + " ".join(
                map(str, [0, 0, 0]))
    
    return infostr


def print_infostate(infostate, annotation, show_probabilities=False):
    
    # For side by side display of top and bottom half of infostate
    split_infostate = [
        infostate[:INITIAL_ARMY], 
        infostate[INITIAL_ARMY:2*INITIAL_ARMY]
        ]
    
    def print_row_half(half_index, i, j):
        if show_probabilities:
            if abs(split_infostate[half_index][i][j]*100) < 100:
                print(f"{round(split_infostate[half_index][i][j]*100):2}", end=' ')
            else:
                print(f"{round(split_infostate[half_index][i][j]):2}", end=' ')
        else:
            # if j < 1 or j > 15:
            print(f"{round(split_infostate[half_index][i][j]):2}", end=' ')

    print("\nInfostate: Opponent Pieces - Allied Pieces")
    if show_probabilities:
        print("Columns: Player-p(1:15)-x-y-floor-ceiling-is_captured")
    else:
        print("Columns: Player-x-y-floor-ceiling-is_captured")

    for i in range(INITIAL_ARMY):
        for j in range(INFOCOLS):
            # Print row of first half
            print_row_half(0, i, j)
        print("  ", end='')
        for j in range(INFOCOLS):
            # Print row of second half
            print_row_half(1, i, j)
        # print piece numbers
        print(f"   {i}+{i+INITIAL_ARMY}", end=" ")
        print()

def main():
    
    # seen = value_permutation_sample(PIECES, sample_size)
    # for permutation in seen:
    #     print(permutation)
    pass
                               

if __name__ == "__main__":
    main()