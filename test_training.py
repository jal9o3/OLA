"""
This is for testing classes and functions in the training module.
"""
import unittest
from core import Board
from training import TimelessBoard


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


if __name__ == '__main__':
    unittest.main()
