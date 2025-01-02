import unittest, random

from generals import *

from infostate_logic import *

class TestInfostateLogic(unittest.TestCase):

    # Test the infostate board function
    def test_infostate_board(self):
        # Generate a random board
        # Instantiate an empty board
        board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
        # Sample random formations
        blue_formation = list(get_random_permutation(FORMATION_COMPONENTS))
        red_formation = list(get_random_permutation(FORMATION_COMPONENTS))

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
        
        # Create the initial infostates
        blue_infostate, blue_infostate_annotation = initial_infostate(board, BLUE)
        red_infostate, red_infostate_annotation = initial_infostate(board, RED)

        # Play a random game
        while not is_terminal(board, annotation):
            # Choose a random move at the current state
            world_actions = actions(board, annotation)
            move = random.choice(world_actions)
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

            # Check if actions count for infostate board equal the world board
            blue_temp = infostate_board(blue_infostate, blue_infostate_annotation)
            red_temp = infostate_board(red_infostate, red_infostate_annotation)
            temp = blue_temp if annotation[CURRENT_PLAYER] == BLUE else red_temp

            # print_board(board)
            # if annotation[CURRENT_PLAYER] == BLUE:
            #     # print_infostate(blue_infostate, blue_infostate_annotation)
            #     # print(blue_infostate)
            #     for row in blue_infostate: print(row)
            # else:
            #     # print_infostate(red_infostate, red_infostate_annotation)
            #     # print(red_infostate)
            #     for row in red_infostate: print(row)
            # print_board(temp[0])
            # print(move)
            # print(results[result])

            infostate_actions = actions(temp[0], temp[1])

            self.assertEqual(len(world_actions), len(infostate_actions))

            # Update infostate
            blue_infostate, blue_infostate_annotation = private_observation(
                blue_infostate, blue_infostate_annotation, move, result)
            red_infostate, red_infostate_annotation = private_observation(
                red_infostate, red_infostate_annotation, move, result
            )

            # Overwrite old state
            board, annotation = new_board, new_annotation

        