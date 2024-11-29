import unittest

from pbs_logic import *

class TestPBSLogic(unittest.TestCase):

    def test_public_observation(self):
        # Define sample PBS
        pbs = [
            [1, 1, 0, 0, 0], [1, 1, 4, 0, 0], [1, 1, 3, 0, 0], [1, 0, 8, 0, 0],
            [1, 1, 8, 0, 0], [1, 3, 0, 1, 0], [1, 0, 0, 0, 0], [1, 2, 3, 0, 0],
            [1, 2, 5, 1, 0], [1, 2, 6, 0, 0], [1, 0, 3, 0, 0], [1, 4, 4, 1, 0],
            [1, 5, 7, 1, 0], [1, 4, 8, 1, 0], [1, 3, 3, 1, 0], [1, 3, 1, 0, 1],
            [1, -1, -1, 1, 1], [1, 3, 1, 0, 1], [1, -1, -1, 1, 1], [1, -1, -1, 0, 1],
            [1, 2, 8, 0, 0],
            [2, 3, 3, 0, 1], [2, 3, 0, 0, 1], [2, 9, 10, 1, 1], [2, 4, 4, 0, 1],
            [2, 9, 10, 2, 1], [2, 5, 7, 0, 1], [2, 4, 8, 0, 1], [2, 4, 1, 0, 0], 
            [2, 4, 2, 0, 0], [2, 6, 0, 0, 0], [2, 2, 5, 0, 1], [2, 5, 3, 0, 0], 
            [2, 6, 4, 0, 0], [2, 7, 8, 0, 0], [2, 5, 8, 0, 0], [2, 7, 1, 0, 0], 
            [2, 7, 3, 0, 0], [2, 6, 2, 0, 0], [2, 3, 1, 2, 0], [2, 6, 7, 0, 0], 
            [2, 6, 8, 0, 0]
        ]
        pbs_annotation = [RED]
        self.assertEqual(len(pbs), 2*INITIAL_ARMY) # Test if PBS size is correct
        # Simulate a public observation
        pbs, pbs_annotation = public_observation(pbs, pbs_annotation, "5857", WIN)
        # Test if PBS has been updated correctly
        # Captured value must equal one
        self.assertEqual(pbs[12][PBS_CAPTURED], 1)
        # Capturer's location and kill count must have updated
        self.assertEqual(pbs[35][PBS_ROW], 5)
        self.assertEqual(pbs[35][PBS_COLUMN], 7)
        self.assertEqual(pbs[35][PBS_KILL_COUNT], 1)
        # Test if annotation has been updated
        self.assertEqual(pbs_annotation[CURRENT_PLAYER], BLUE)
