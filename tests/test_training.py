"""
This is for testing classes and functions in the training module.
"""

import sys
import os

import unittest
from OLA.core import Board, Player
from OLA.training import TimelessBoard, ActionsFilter

testdir = os.path.dirname(__file__)
SRCDIR = '../OLA'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, SRCDIR)))


class TestTimelessBoard(unittest.TestCase):
    """
    This is for testing the TimelessBoard class.
    """

    def test_actions(self):
        """
        This is for testing the actions method.
        """
        timeless_board = TimelessBoard()
        actions = timeless_board.actions()

        # Check if the actions list is not empty
        self.assertTrue(len(actions) > 0)

        # Check if the actions are in the correct format
        for action in actions:
            self.assertEqual(len(action), 4)
            self.assertTrue(action.isdigit())

        # Check if the actions are within the board boundaries
        for action in actions:
            start_row, start_col, end_row, end_col = map(int, action)
            self.assertTrue(0 <= start_row < Board.ROWS)
            self.assertTrue(0 <= start_col < Board.COLUMNS)
            self.assertTrue(0 <= end_row < Board.ROWS)
            self.assertTrue(0 <= end_col < Board.COLUMNS)

        self.assertEqual(len(actions), 254)


class TestActionsFilter(unittest.TestCase):
    """
    This is for testing the ActionsFilter class.
    """

    def test_move_ordering(self):
        """
        This is for making sure the move ordering works as intended.
        """
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 16, 0],
            [0, 0, 0, 0, 0, 0, 2, 0, 0],
            [0, 0, 15, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        actions_filter = ActionsFilter(state=sample_board, directions=None,
                                       square_whitelist=None)

        self.assertEqual(len(sample_board.actions()),
                         len(actions_filter.move_ordering()))

        sample_board = Board(sample_state_matrix, player_to_move=Player.RED,
                             blue_anticipating=False, red_anticipating=False)
        actions_filter = ActionsFilter(state=sample_board, directions=None,
                                       square_whitelist=None)

        print(sample_board.actions())
        print(actions_filter.move_ordering())
        
        self.assertEqual(len(sample_board.actions()),
                         len(actions_filter.move_ordering()))


if __name__ == '__main__':
    unittest.main()
