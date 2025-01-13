import logging, copy, random, json, os, ctypes, csv, time, itertools

from ctypes import c_int, c_double

from collections import deque

from functools import partial

# Configure the logging
logging.basicConfig(level=logging.WARNING)

# World constants
from world_constants import *
from infostate_constants import *

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

def transition(action, board=None, annotation=None):
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

    # print(action)

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


# Give utility estimates to nonterminal board estimates
# NOTE: Reward is from the perspective of BLUE (negative values are pro-RED)
def reward_estimate(board, annotation):
    # Initialize the utility value
    utility = 0

    # Estimated rewards for features
    capture_reward = 0.08
    push_reward = 0.08
    # flag_safety_reward = 0.02 # 0.30/(ROWS - 1 + COLUMNS - 1)
    flag_safety_reward = 0.09 # Often difference between winning and losing!

    total_firepower = 145 # Sum of rankings of all pieces in an army
    blue_firepower = 0
    red_firepower = 0
    
    # Rewards for captured and pushed pieces
    blue_pieces = 0
    red_pieces = 0
    # Count BLUE and RED pieces
    for i, row in enumerate(board):
        for j, square in enumerate(row):
            # Check if the piece is BLUE or RED
            if FLAG <= square <= SPY:
                # blue_pieces +=1
                blue_firepower += square
                # Reward based on the piece's row
                utility += i*push_reward
            elif FLAG + SPY <= square <= SPY + SPY:
                # red_pieces += 1
                red_firepower += square - SPY
                # Reward based on the piece's row
                utility += -((ROWS-i)*push_reward)

    # Reward the player based on their remaining firepower
    utility += (blue_firepower/total_firepower)*capture_reward
    utility += -((red_firepower/total_firepower)*capture_reward)


    # Reward estimates for flag safety
    blue_flag = find_integer(board, FLAG)
    red_flag = find_integer(board, FLAG + SPY)
    nearest_red = find_nearest_in_range_bfs(
        board, blue_flag[0], blue_flag[1], FLAG + SPY, SPY*2)
    nearest_blue = find_nearest_in_range_bfs(
        board, red_flag[0], red_flag[1], FLAG, SPY)
    # Calculate the Manhattan distance of nearest enemy to each flag
    blue_manhattan = abs(
        nearest_red[0] - blue_flag[0]) + abs(nearest_red[1] - blue_flag[1])
    red_manhattan = abs(
        nearest_blue[0] - red_flag[0]) + abs(nearest_blue[1] - red_flag[1])
    
    utility += blue_manhattan*flag_safety_reward + 0.30
    utility += -(red_manhattan*flag_safety_reward + 0.30)

    # Find the value of the flag's "protector"
    blue_protector = max_in_range(board, blue_flag, nearest_red, PRIVATE, SPY)
    red_protector = max(max_in_range(board, red_flag, nearest_blue, 
                                 PRIVATE + SPY, SPY*2) - SPY, 0)
    utility += blue_protector*flag_safety_reward
    utility += -(red_protector*flag_safety_reward)

    # Measure flag "freedom"
    # Check count of pieces in the flag's direct path
    blue_flagblocks = count_nonzero_neighbors(board, blue_flag[0], blue_flag[1])
    red_flagblocks = count_nonzero_neighbors(board, red_flag[0], red_flag[1])
    # If the flag is not at the starting edge, check neighbors of square behind it
    if blue_flag[0] > 0:
        blue_flagblocks += count_nonzero_neighbors(board, blue_flag[0] - 1, blue_flag[1])
    if red_flag[0] < 7:
        red_flagblocks += count_nonzero_neighbors(board, red_flag[0] + 1, red_flag[1])

    utility += -(blue_flagblocks*flag_safety_reward)
    utility += red_flagblocks*flag_safety_reward


    return utility

"""
Example usage
matrix = [
    [1, 0, 3],
    [0, 5, 0],
    [7, 0, 9]
]
row, col = 1, 1  # position (1, 1) in the matrix

print(count_nonzero_neighbors(matrix, row, col))  # Output will be 0
"""
def count_nonzero_neighbors(matrix, row, col):
    rows = len(matrix)
    cols = len(matrix[0])
    nonzero_count = 0

    # Define the directions for up, down, left, and right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        # Check if the new position is within bounds
        if 0 <= new_row < rows and 0 <= new_col < cols:
            if matrix[new_row][new_col] != 0:
                nonzero_count += 1

    return nonzero_count


"""
Example usage
matrix = [
    [10, 20, 30],
    [40, 50, 60],
    [70, 80, 90]
]
target = 50

result = find_integer(matrix, target)
print(result)  # Output: (1, 1) because 50 is located at row 1, column 1
"""
def find_integer(matrix, target):
    for row in range(len(matrix)):
        for col in range(len(matrix[row])):
            if matrix[row][col] == target:
                return (row, col)
    return None

"""
Example usage
matrix = [
    [10, 20, 30],
    [40, 50, 60],
    [70, 80, 90]
]
target_row = 1
target_column = 1
MIN = 35
MAX = 75

result = find_nearest_in_range_bfs(matrix, target_row, target_column, MIN, MAX)
print(result)  # Output: (2, 0) because 70 is the nearest element in range [35, 75] 
               # to element (1, 1)
"""
def find_nearest_in_range_bfs(matrix, target_row, target_column, MIN, MAX):
    def is_in_range(value):
        return MIN <= value <= MAX
    
    rows = len(matrix)
    cols = len(matrix[0])
    visited = [[False] * cols for _ in range(rows)]
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    queue = deque([(target_row, target_column, 0)])  # (row, column, distance)
    visited[target_row][target_column] = True
    
    while queue:
        r, c, dist = queue.popleft()
        
        if is_in_range(matrix[r][c]):
            return (r, c)
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr][nc]:
                visited[nr][nc] = True
                queue.append((nr, nc, dist + 1))
    
    return None

"""
Example Usage
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
square_a = (0, 0)  # Row 0, Column 0
square_b = (2, 2)  # Row 2, Column 2
min_val = 4
max_val = 8

result = max_in_range(matrix, square_a, square_b, min_val, max_val)
print(f"Maximum value in range [{min_val}, {max_val}]: {result}")
"""
def max_in_range(matrix, square_a, square_b, min_val, max_val):
    # Extract the row and column indices
    row1, col1 = square_a
    row2, col2 = square_b

    # Determine the bounds of the sub-matrix
    top = min(row1, row2)
    bottom = max(row1, row2)
    left = min(col1, col2)
    right = max(col1, col2)

    # Flatten the sub-matrix using itertools.chain
    flattened_sub_matrix = itertools.chain.from_iterable(
        row[left:right + 1] for row in matrix[top:bottom + 1]
    )
    flattened_list = list(flattened_sub_matrix)
    # print(flattened_list)

    # Filter values within the range [min_val, max_val]
    filtered_values = [value for value in flattened_list if min_val <= value <= max_val]
    # print(filtered_values)
    

    # Find the maximum value, or return None if no values are in range
    return max(filtered_values, default=0)

# Adapt counterfactual regret minimization to GG
# For external sampling, set traverser to BLUE or RED
# Obtained policies can be stored in a dictionary via the policy_table parameter
# Set policy_table to None if policies will not be stored
def cfr(board, annotation, blue_probability, red_probability,
        blue_infostate, blue_infostate_annotation,
        red_infostate, red_infostate_annotation,
        current_depth=0, max_depth=0, turn_number=0, traverser=0,
        policy_table=None, utility_table=None,
        utility_model=None, policy_model=None):

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    player = annotation[CURRENT_PLAYER]

    # Obtain the current player's infostate
    if player == BLUE:
        relevant_infostate, relevant_infostate_annotation = blue_infostate, blue_infostate_annotation
    else:
        relevant_infostate, relevant_infostate_annotation = red_infostate, red_infostate_annotation

    # Convert the infostate to a string for storage in the dictionary
    if policy_table != None:
        infostate_key = infostate_to_string(relevant_infostate, relevant_infostate_annotation)

    # Return payoff for 'terminal' states
    if ((current_depth == max_depth and is_terminal(board, annotation))
         or is_terminal(board, annotation)):
        if player == BLUE:
            # Store the utility in the utility table
            if utility_table != None:
                utility_table[infostate_key] = reward(board, annotation)
            return reward(board, annotation), []
        else:
            # Store the utility in the utility table
            if utility_table != None:
                utility_table[infostate_key] = -reward(board, annotation)
            return -(reward(board, annotation)), []
    elif current_depth == max_depth and not is_terminal(board, annotation):
        if player == BLUE:
            return reward_estimate(board, annotation), []
        else:
            return -(reward_estimate(board, annotation)), []

    # Initialize strategy
    valid_actions = actions(board, annotation)
    actions_n = len(valid_actions)

    # Obtain policy from policy table if any
    if policy_table != None:
        if infostate_key in policy_table:
            strategy = policy_table[infostate_key][0]
        # Use the policy network to obtain probability estimates
        elif policy_model != None:
          # Concatenate the infostate strings with the move representations
          # Iterate through the actions
          strategy = [0.0 for i in range(actions_n)] # Prepare empty strategy
          for i, action in enumerate(valid_actions):
            infostate_and_action = ""
            infostate_and_action += infostate_key # Infostate representation

            for j in range(4): # Length of an action representation
                infostate_and_action += " " + action[j] # Concatenation

            # Convert concatenated string to list
            concatlist = infostate_and_action.split()
            # Convert list to np array
            concatarray = np.array(concatlist, dtype=np.float32)
            # Convert np array to Pytorch tensor
            concatensor = torch.tensor(concatarray)
            concatensor = concatensor.to(device)
            # Reshape the tensor to what is expected of the policy network
            concatensor = concatensor.view(1, -1)
            probability = policy_model(concatensor) # Obtain the probability estimate
            strategy[i] = probability.item() # Store the estimate in the strategy

            # Sanitize the strategy
            for i in range(len(strategy)):
              if strategy[i] < 0:
                strategy[i] = 0
            if sum(strategy) <= 0:
              strategy = [1.0/actions_n for i in range(actions_n)] # Uniform strategy
        else:
            strategy = [1.0/actions_n for i in range(actions_n)] # Uniform strategy
    else:
        strategy = [1.0/actions_n for i in range(actions_n)] # Uniform strategy
    regret_sum = [0.0 for i in range(actions_n)]

    # Initialize action utilities
    util = [0.0 for i in range(actions_n)]
    # Initialize node utility
    node_util = 0

    
    # Create a partial transition function that sets the current state as constant
    transition_current = partial(transition, board=board, annotation=annotation)
    # Map transition function to all valid actions to obtain the children nodes
    next_states = list(map(transition_current, valid_actions))
    # Create a partial result function, current state as constant
    get_result_current = partial(get_result, board=board, annotation=annotation)
    # Map result function to the children nodes
    action_results = list(map(get_result_current, valid_actions, 
                  [state[0] for state in next_states], 
                  [state[1] for state in next_states]))
    # Create partial private observation functions for BLUE and RED
    blue_private_observation = partial(private_observation, 
                                       old_infostate=blue_infostate, 
                                       old_infostate_annotation=blue_infostate_annotation)
    red_private_observation = partial(private_observation,
                                      old_infostate=red_infostate,
                                      old_infostate_annotation=red_infostate_annotation)
    # Map private observation functions to infostates and actions and results
    next_blue_infostates = list(map(blue_private_observation, valid_actions, 
                                    action_results))
    next_red_infostates = list(map(red_private_observation, valid_actions, 
                                   action_results))

    # Assign probabilities
    def assign_probabilities(strategy_weight, player=None):
        if player == BLUE:
            # probability_A = red_probability * strategy[a]
            probability_A = blue_probability * strategy_weight
            probability_B = red_probability
        else:
            probability_A = blue_probability
            # probability_B = red_probability * strategy[a]
            probability_B = red_probability * strategy_weight
        
        return probability_A, probability_B
    
    # Create partial probability assignment function
    assign_probabilities_current = partial(assign_probabilities, player=player)

    # Map probability assignment function to list of strategy probabilities
    probabilities = list(map(assign_probabilities_current, strategy))

    # Create partial CFR that sets some parameters constant
    cfr_current = partial(cfr, 
                          current_depth=current_depth + 1, max_depth=max_depth,
                          traverser=traverser, 
                          policy_table=policy_table, utility_table=utility_table,
                          utility_model=utility_model, policy_model=policy_model)    
    # Map CFR to list of children nodes
    results = list(map(cfr_current, 
                       [state[0] for state in next_states], 
                       [state[1] for state in next_states],
                       [probability_pair[0] for probability_pair in probabilities],
                       [probability_pair[1] for probability_pair in probabilities],
                       [infostate[0] for infostate in next_blue_infostates],
                       [infostate[1] for infostate in next_blue_infostates],
                       [infostate[0] for infostate in next_red_infostates],
                       [infostate[1] for infostate in next_red_infostates]))

    # Obtain the calculated utilities for each child node
    util = [-(result[0]) for result in results]
    
    # Weighting by strategy
    def weight_utility(strategy_weight, utility_value):
        return strategy_weight*utility_value
    
    node_sub_utilities = list(map(weight_utility, util, strategy))
    node_util = sum(node_sub_utilities)


    # ORIGINAL IMPLEMENTATION OF RECURSION:
    """
    # Iterate over children nodes and recursively call cfr
    for a, action in enumerate(valid_actions):
        next_board, next_annotation = transition(board=board, 
                                                 annotation=annotation, action=action)
        action_result = get_result(board=board, annotation=annotation, 
                                   move=action, new_board=next_board, 
                                   new_annotation=next_annotation)
        next_blue_infostate, next_blue_infostate_annotation = private_observation(
            old_infostate=blue_infostate, 
            old_infostate_annotation=blue_infostate_annotation, 
            action=action, result=action_result)
        next_red_infostate, next_red_infostate_annotation = private_observation(
            old_infostate=red_infostate, 
            old_infostate_annotation=red_infostate_annotation, 
            action=action, result=action_result)
        
        if player == BLUE:
            probability_A = red_probability * strategy[a]
            probability_B = blue_probability
        else:
            probability_A = blue_probability
            probability_B = red_probability * strategy[a]

        result = cfr(next_board, next_annotation,
                    probability_A, probability_B,
                    next_blue_infostate, next_blue_infostate_annotation,
                    next_red_infostate, next_red_infostate_annotation,
                    current_depth=current_depth + 1, max_depth=max_depth, 
                    traverser=traverser, 
                    policy_table=policy_table, utility_table=utility_table,
                    utility_model=utility_model, policy_model=policy_model)
        util[a] = -(result[0])

        # Calculate node utility
        node_util += strategy[a] * util[a]
    """

    # Calculate regret sum
    for a, action in enumerate(valid_actions):
        logger.setLevel(logging.DEBUG)
        regret = util[a] - node_util
        regret_sum[a] += (red_probability if player == RED else blue_probability) * regret

    # Normalize regret sum to find strategy for this node
    strategy = [0.0 for i in range(actions_n)]
    normalizing_sum = sum(regret_sum)
    for a, action in enumerate(valid_actions):
        if regret_sum[a] > 0:
            normalizing_sum += regret_sum[a]

    for a, action in enumerate(valid_actions):
        if normalizing_sum > 0:
            strategy[a] = regret_sum[a] / normalizing_sum
        else:
            strategy[a] = 1.0 / actions_n

        # Update node utility with regret-matched strategy
        node_util += strategy[a] * util[a]

    # Store the policy in the policy_table
    if policy_table != None and utility_table != None:
        policy_table[infostate_key] = (strategy, valid_actions, turn_number)
        utility_table[infostate_key] = node_util

    # Return node utility
    return node_util, strategy

# Training loop for CFR
def cfr_train(board, annotation, blue_probability, red_probability,
              blue_infostate, blue_infostate_annotation,
              red_infostate, red_infostate_annotation,
              current_depth=0, max_depth=0, turn_number=0, iterations=3,
              policy_table=None, utility_table=None,
              utility_model=None, policy_model=None):

    start_time = time.time()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Print the nearest enemy pieces to the flags
    # blue_flag = find_integer(board, FLAG)
    # red_flag = find_integer(board, SPY + FLAG)
    # print("Nearest to BLUE flag:")
    # print(find_nearest_in_range_bfs(board, blue_flag[0], blue_flag[1], FLAG + SPY, SPY*2))
    # print("Nearest to RED flag:")
    # print(find_nearest_in_range_bfs(board, red_flag[0], red_flag[1], FLAG, SPY))

    traverser = BLUE
    utility_sum = 0.0
    strategy_sum = [0.0 for i in range(len(actions(board, annotation)))]

    for i in range(iterations):
        # start_time = time.time()
        util, strategy = cfr(board, annotation, 
                             blue_probability, red_probability,
                             blue_infostate, blue_infostate_annotation,
                             red_infostate, red_infostate_annotation,
                             current_depth=current_depth, max_depth=max_depth, 
                             policy_table=policy_table, utility_table=utility_table,
                             utility_model=utility_model, policy_model=policy_model, 
                             turn_number=turn_number)
        # end_time = time.time()
        # print(f"Runtime: {end_time - start_time} seconds")

        # Add strategy to strategy sum
        for i in range(len(actions(board, annotation))):
            if strategy[i] > 0:
                strategy_sum[i] += strategy[i]
        # Add utility to utility sum
        # if annotation[CURRENT_PLAYER] == RED:
        #     util *= -1
        utility_sum += util
        # Switch to next traverser
        traverser = RED if traverser == BLUE else BLUE

    # Normalize the strategy sum
    accumulated = 0.0
    for i in range(len(actions(board, annotation))):
        accumulated += strategy_sum[i]
    for i in range(len(actions(board, annotation))):
        strategy_sum[i] /= accumulated
    # Calculate the average utility
    average_utility = utility_sum / iterations

    end_time = time.time()
    print(f"Runtime: {end_time - start_time} seconds")

    return average_utility, strategy_sum

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
    # # Obtain initial probabilities
    range_offset = 0 if player == BLUE else SPY # for finding the correct columns
    for piece in range(INITIAL_ARMY):
        for col in range(INFOCOLS):
            if col == PLAYER:
                infostate[piece][col] = RED if player == BLUE else BLUE
            # elif range_start - range_offset <= col <= range_end - range_offset:
            #     if col == PRIVATE:
            #         infostate[piece][col] = 6/INITIAL_ARMY
            #     elif col == SPY:
            #         infostate[piece][col] = 2/INITIAL_ARMY
            #     else:
            #         infostate[piece][col] = 1/INITIAL_ARMY
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
                # infostate[piece_n][value] = 1
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
