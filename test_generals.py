import unittest, json

from generals import *

class TestGenerals(unittest.TestCase):
    
    # Test the reward function
    def test_reward(self):
        # Load a sample terminal state
        with open(f'world_samples/red_captured.json', 'r') as file:
            state_data = json.load(file)
        board = state_data[0]
        annotation = state_data[1]

        # Assert expected rewards
        self.assertEqual(reward(board, annotation), 1)