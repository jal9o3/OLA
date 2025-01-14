"""
These unit tests ensure that critical components of the OLA engine remain
operational throughout continued development.
"""
import unittest
from unittest.mock import patch

from core import Board, Player, Ranking, get_random_permutation


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
        player = Player(Board.BLUE_PLAYER)
        self.assertEqual(player.color, Board.BLUE_PLAYER)
        player = Player(Board.RED_PLAYER)
        self.assertEqual(player.color, Board.RED_PLAYER)

    def test_get_random_formation(self):
        """
        This test makes sure that the random formation has the required number 
        of pieces and spaces.
        """
        piece_list = Ranking.SORTED_FORMATION
        self.assertEqual(len(Player.get_random_formation(
            piece_list)), len(Ranking.SORTED_FORMATION))


class TestGetRandomPermutation(unittest.TestCase):
    @patch('core.random.shuffle')
    def test_get_random_permutation(self, mock_shuffle):
        elements = [1, 2, 3]
        # Mocking shuffle to reverse the list
        mock_shuffle.side_effect = lambda x: x.reverse()
        result = get_random_permutation(elements)
        self.assertEqual(result, (3, 2, 1))

    def test_get_random_permutation_type(self):
        elements = [1, 2, 3]
        result = get_random_permutation(elements)
        self.assertIsInstance(result, tuple)


if __name__ == '__main__':
    unittest.main()
