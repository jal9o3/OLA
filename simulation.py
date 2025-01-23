import logging, copy, random, json, os, ctypes, csv, time, itertools

from ctypes import c_int, c_double

from collections import deque

from functools import partial

# Configure the logging
logging.basicConfig(level=logging.WARNING)

# World constants
from world_constants import *

# Infostate related functions
from infostate_logic import *

# Public belief state related functions
from pbs_logic import *

# from world_constants import *

from generals import *

from gg_train import CFR

class CFRResult(ctypes.Structure): 
    _fields_ = [("node_util", ctypes.c_double), 
                ("strategy", ctypes.POINTER(ctypes.c_double))]

# Parameter save_game=True if game data will be saved
# available modes: HUMAN_VS_RANDOM, RANDOM_VS_RANDOM, CFR_VS_CFR
def simulate_game(blue_formation, red_formation, mode=CFR_VS_CFR,
                  cfr=CFR.train, c=False, save_game=True,
                  utility_model=None, policy_model=None):
    
    start_time = time.time()
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Board for arbiter
    board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    annotation = [BLUE, 0, 0]

    # Boards for both player POVs
    blue_board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    red_board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]

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

    # pbs, pbs_annotation = initial_pbs(board)

    # Gameplay loop
    # mode = RANDOM_VS_RANDOM
    # mode = HUMAN_VS_RANDOM
    # mode = CFR_VS_CFR
    t = 0
    moves_N = 0 # total number of branches found
    if mode == HUMAN_VS_RANDOM:
        human = random.choice([BLUE, RED])
        print(f"You are player {human}")
    else:
        human = 0

    if save_game:
        move_history = [] # Initialize list of moves

    # C standard library
    libc = ctypes.CDLL("libc.so.6")
    free = libc.free
    free.argtypes = [ctypes.c_void_p]

    # Initialize tables for CFR
    if mode == CFR_VS_CFR:
        policy_table = dict()
        utility_table = dict()

    while not is_terminal(board, annotation):
        print(f"Turn: {t + 1}")

        if mode == RANDOM_VS_RANDOM:
            print_board(board, color=True, pov=WORLD)
            # print_infostate(blue_infostate, blue_infostate_annotation)
            # print_infostate(red_infostate, red_infostate_annotation)
            print_pbs(pbs, pbs_annotation)
        elif mode == HUMAN_VS_RANDOM:
            print_board(board, color=True, pov=human)
            print_pbs(pbs, pbs_annotation)
        elif mode == CFR_VS_CFR:
            # print_infostate(blue_infostate, blue_infostate_annotation)
            # print_infostate(red_infostate, red_infostate_annotation)
            print_board(board, color=True, pov=WORLD)
            magnitude = -1 if annotation[CURRENT_PLAYER] == RED else 1
            # print(f"Estimate: {magnitude*reward_estimate(board, annotation)}")

        print(f"Player: {annotation[CURRENT_PLAYER]}")
        moves = actions(board, annotation)
        # print(moves)
        moves_N += len(moves)
        print(f"Possible Moves: {len(moves)}")
        move = ""
        if mode == HUMAN_VS_RANDOM and annotation[CURRENT_PLAYER] == human:
            while move not in moves:
                move = input("Move: ")
        elif mode == RANDOM_VS_RANDOM:
            move = random.choice(moves)
        elif mode == CFR_VS_CFR:

            if len(moves) <= 6:
                max_depth = 4
            elif len(moves) <= 3:
                max_depth = 8
            else:
                max_depth = 2

            # max_depth *= 2
            # max_depth += 1

            logger.setLevel(logging.DEBUG)
            print(f"Solving to depth {max_depth}...")

            if c:
                # Convert the 2D list to a ctypes array
                board_type = (ctypes.c_int * COLUMNS) * ROWS
                # Ctypes array for annotation
                annotation_type = (ctypes.c_int * 3)

                c_board = board_type()
                c_annotation = annotation_type()
                for i in range(ROWS):
                    for j in range(COLUMNS):
                        c_board[i][j] = board[i][j]

                for i in range(3):
                    c_annotation[i] = annotation[i]

            if not c:
                # util, strategy = cfr(board, annotation, 1, 1,
                #                      blue_infostate, blue_infostate_annotation,
                #                      red_infostate, red_infostate_annotation, 
                #                      current_depth=0, max_depth=max_depth,
                #                      policy_table=policy_table,
                #                      utility_table=utility_table,
                #                      utility_model=utility_model,
                #                      policy_model=policy_model,
                #                      turn_number=t)
                util = 0
                strategy = cfr(board, annotation, moves)
            elif c:
                result = cfr(c_board, c_annotation, 1, 1, 0, max_depth)
                util = result.node_util
                c_strategy = result.strategy
                strategy = [c_strategy[i] for i in range(len(moves))]
                # Remove strategy array from memory
                free(result.strategy)

            # print("Strategy: ")
            # for i, s in enumerate(strategy):
            #     print(f"{round(s*100)}%", end=' ')
            # print()
            # print(strategy)
            # print(f"Strategy Sum: {sum(strategy):.2f}")

            player_tags = ["ARBITER", "BLUE", "RED"]

            print(f"{player_tags[annotation[CURRENT_PLAYER]]}'s Utility: {util:.2f}")

            # Set negative weights to zero to avoid errors
            for a, action in enumerate(strategy):
                if action < 0:
                    strategy[a] = 0

            # # Only consider the top three moves
            # sorted_strategy = sorted(strategy, reverse=True) # descending order
            # # Get a list of the top three values
            # top_three = sorted_strategy[:3]
            # # Set all values below top three to zero (removes too suboptimal moves)
            # for a, action in enumerate(strategy):
            #     if action not in top_three:
            #         strategy[a] = 0

            # Set probability to zero if not within a standard deviation of max
            mean = sum(strategy) / len(strategy)
            variance = sum((p - mean) ** 2 for p in strategy) / len(strategy)
            std_dev = variance ** 0.5
            max_prob = max(strategy)
            # Set a threshold for "within a standard deviation" of the highest probability
            threshold = std_dev
            # Zero out probabilities not within the threshold
            strategy = [prob if abs(prob - max_prob) <= threshold else 0 for prob in strategy]

            # Renormalize the sanitized strategy
            strategy_sum = sum(strategy)
            for a, action in enumerate(strategy):
                strategy[a] = strategy[a]/strategy_sum
            # print("Sanitized Strategy: ")
            # for i, s in enumerate(strategy):
            #     print(f"{round(s*100)}%", end=' ')
            # print()
            # print(strategy)
            # Print the remaining moves in sanitized strategy
            # print("Remaining Moves:")
            # for i, action in enumerate(moves):
            #     if strategy[i] > 0:
            #         print(f"{action}", end=" ")
            #     else:
            #         print("XXXX", end=" ")
            # print()

            move = random.choices(moves, weights=strategy, k=1)[0]

        print(f"Chosen Move: {move}")

        # Handle the saving of game moves
        if save_game:
            move_history.append(move)

        new_board, new_annotation = transition(board=board, 
                                               annotation=annotation, 
                                               action=move)
        # Examine move result (WIN, LOSS, TIE)
        result = get_result(board=board, annotation=annotation, move=move, 
                            new_board=new_board, new_annotation=new_annotation)

        # Update infostates
        blue_infostate, blue_infostate_annotation = private_observation(
            old_infostate=blue_infostate, 
            old_infostate_annotation=blue_infostate_annotation, 
            action=move, result=result)
        red_infostate, red_infostate_annotation = private_observation(
            old_infostate=red_infostate, 
            old_infostate_annotation=red_infostate_annotation, 
            action=move, result=result
        )

        # Update PBS
        # pbs, pbs_annotation = public_observation(pbs, pbs_annotation, move, result)

        # Overwrite old state
        board, annotation = new_board, new_annotation

        t += 1

    outcomes = ["DRAW", "BLUE", "RED"]
    print(f"Winner: {outcomes[reward(board, annotation)]}")

    # Handle saving of latest game to a JSON file
    if save_game:
        game_data.append(move_history)
        os.makedirs('history', exist_ok=True)
        with open('history/latest_game.json', 'w') as file:
            json.dump(game_data, file)
    print(f"Average branching: {round(moves_N/t)}")

    end_time = time.time()
    print(f"Game Runtime: {((end_time - start_time)/60):.2f} minutes")

    return policy_table, utility_table, t

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Sample random formation
    blue_formation = list(get_random_permutation(FORMATION_COMPONENTS))
    red_formation = list(get_random_permutation(FORMATION_COMPONENTS))

    faster = ctypes.CDLL('./cfr.so')

    # Ctypes array for annotation
    annotation = (ctypes.c_int * 3)
    # Convert the 2D list to a ctypes array 
    board = (ctypes.c_int * COLUMNS) * ROWS
    
    # Define the argument and return types of the C function 
    faster.cfr.argtypes = [board, annotation, c_double, c_double, c_int, c_int] 
    faster.cfr.restype = CFRResult

    # simulate_game(blue_formation, red_formation, cfr=faster.cfr, c=True)

    # policy_table, utility_table, turns_taken = simulate_game(blue_formation, red_formation, cfr=cfr_train)

    policy_table, utility_table, turns_taken = simulate_game(blue_formation, red_formation)

    # print(len(policy_table))
    # print(len(utility_table))

    rows = 0

    print("Writing to utility.csv...")
    # Write utility table contents to utility.csv
    with open('utility.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['Infostate', 'Utility'])
        # Write the data
        for key, value in utility_table.items():
            writer.writerow([key, value])
            rows += 1

    print(f"Utility data ({rows} rows) successfully written to utility.csv")

    rows = 0

    print("Writing to policy.csv...")
    # Write policy table contents to policy.csv
    with open('policy.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['InfostateAction', 'Probability'])
        # Write the data
        for key, value in policy_table.items():
            # Iterate through the actions in the infostate
            for i in range(len(value[0])): # Size of policy vector
                infostate_and_action = ""
                infostate_and_action += key # Infostate representation
                for j in range(4): # Length of an action representation
                    infostate_and_action += " " + value[1][i][j] # Concatenate infostate and action representation
                writer.writerow([infostate_and_action, value[0][i]])
                rows += 1

    print(f"Policy data ({rows} rows) successfully written to policy.csv")


    # simulate_game(blue_formation, red_formation)

if __name__ == "__main__":
    main()