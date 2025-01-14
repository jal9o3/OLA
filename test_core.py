"""
These unit tests ensure that critical components of the OLA engine remain
operational throughout continued development.
"""
import unittest
from unittest.mock import patch

from core import Player, Ranking, get_random_permutation


class TestPlayer(unittest.TestCase):
    """
    This tests the Player class, which handles player related functions such as
    sampling valid formations.
    """

    def test_initial_color(self):
        """
        This makes sure that the Player instance can be designated to a valid
        side.
        """
        player = Player(Player.BLUE)
        self.assertEqual(player.color, Player.BLUE)
        player = Player(Player.RED)
        self.assertEqual(player.color, Player.RED)

    def test_get_random_formation(self):
        """
        This test makes sure that the random formation has the required number 
        of pieces and spaces.
        """
        piece_list = Ranking.SORTED_FORMATION
        self.assertEqual(len(Player.get_random_formation(
            piece_list)), len(Ranking.SORTED_FORMATION))


class TestGetRandomPermutation(unittest.TestCase):
    """
    This tests the function that shuffles any given list.
    """
    @patch('core.random.shuffle')
    def test_get_random_permutation(self, mock_shuffle):
        """
        This test simulates a random shuffle.
        """
        elements = [1, 2, 3]
        # Mocking shuffle to reverse the list
        mock_shuffle.side_effect = lambda x: x.reverse()
        result = get_random_permutation(elements)
        self.assertEqual(result, (3, 2, 1))

    def test_get_random_permutation_type(self):
        """
        This test verifies that the function returns a result of the proper
        type and length.
        """
        elements = [1, 2, 3]
        result = get_random_permutation(elements)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(elements), len(result))


if __name__ == '__main__':
    unittest.main()
