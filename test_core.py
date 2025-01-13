# test_player.py
import unittest
from core import Player, get_random_permutation
from unittest.mock import patch

class TestPlayer(unittest.TestCase):
    def test_initial_color(self):
        player = Player(1)
        self.assertEqual(player.color, 1)

    @patch('core.get_random_permutation')
    def test_get_random_formation(self, mock_get_random_permutation):
        mock_get_random_permutation.return_value = [2, 1, 3]
        piece_list = [1, 2, 3]
        self.assertEqual(Player.get_random_formation(piece_list), [2, 1, 3])
        mock_get_random_permutation.assert_called_once_with(piece_list)

if __name__ == '__main__':
    unittest.main()
