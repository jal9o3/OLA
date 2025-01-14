import unittest
from unittest.mock import patch

from core import Player, get_random_permutation


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
