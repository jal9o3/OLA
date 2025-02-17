"""
These unit tests ensure that critical components of the OLA engine remain
operational throughout continued development.
"""
import unittest
from unittest.mock import patch


from helpers import (get_random_permutation, get_blank_matrix,
                     get_hex_uppercase_string)
from constants import Result, Ranking
from core import Board, Infostate, Player


class TestGetRandomPermutation(unittest.TestCase):
    """
    This tests the function that shuffles any given list.
    """
    @patch('helpers.random.shuffle')
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


class TestGetBlankMatrix(unittest.TestCase):
    """
    This tests whether the get_blank_matrix function returns a matrix with the
    correct number of rows and columns, with all entries set to zero.
    """

    def test_matrix_size(self):
        """
        This checks the number of rows and columns.
        """
        rows, columns = 3, 4
        matrix = get_blank_matrix(rows, columns)
        self.assertEqual(len(matrix), rows)
        self.assertTrue(all(len(row) == columns for row in matrix))

    def test_matrix_entries(self):
        """
        This checks whether all the entries are set to zero.    `
        """
        rows, columns = 3, 4
        matrix = get_blank_matrix(rows, columns)
        for row in matrix:
            self.assertTrue(all(entry == 0 for entry in row))


class TestHexUppercaseString(unittest.TestCase):
    """
    This test ensures that the conversion to uppercase hex representations
    works as expected.
    """

    def test_single_digit(self):
        """
        Try to convert the number 5.
        """
        self.assertEqual(get_hex_uppercase_string(5), '5')

    def test_double_digit(self):
        """
        Try to convert the number 15.
        """
        self.assertEqual(get_hex_uppercase_string(15), 'F')

    def test_triple_digit(self):
        """
        Try to convert the number 255.
        """
        self.assertEqual(get_hex_uppercase_string(255), 'FF')


class TestBoard(unittest.TestCase):
    """
    This tests the Board class, which represents the game state as seen by the
    arbiter, and handles all related functionality such as managing clashes
    between opposing pieces.
    """

    def test_blue_player(self):
        """
        Check if affiliations are correctly identified for the blue ranking 
        range.
        """
        for piece in range(1, 16):
            self.assertEqual(Board.get_piece_affiliation(piece), Player.BLUE)

    def test_red_player(self):
        """
        Check if affiliations are correctly identified for the red ranking 
        range.
        """
        for piece in range(16, 31):
            self.assertEqual(Board.get_piece_affiliation(piece), Player.RED)

    def test_label_piece_by_team(self):
        """
        This tests if the pieces are correctly labelled according to their rank
        and team.
        """
        for piece in range(1, 16):
            expected = "b" + get_hex_uppercase_string(piece)
            self.assertEqual(Board.label_piece_by_team(piece), expected)

        for piece in range(16, 31):
            expected = "r" + get_hex_uppercase_string(piece - Ranking.SPY)
            self.assertEqual(Board.label_piece_by_team(piece), expected)

    def test_actions(self):
        """
        This checks if the possible actions in the given game state are
        enumerated as expected.
        """
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 2, 0, 0],
            [0, 0, 15, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 16, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        self.assertEqual(len(sample_board.actions()), 16)
        sample_board = Board(sample_state_matrix, player_to_move=Player.RED,
                             blue_anticipating=False, red_anticipating=False)
        self.assertEqual(len(sample_board.actions()), 12)

    def test_reward(self):
        """
        This verifies that the proper values are assigned to terminal states.
        """
        win_value = 1000000
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 2, 0, 0],
            [0, 0, 15, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.RED,
                             blue_anticipating=False, red_anticipating=False)
        self.assertEqual(sample_board.reward(), -win_value)
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 2, 0, 0],
            [0, 0, 15, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 16, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        self.assertEqual(sample_board.reward(), -win_value)
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 2, 0, 0],
            [0, 0, 15, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 16, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.RED,
                             blue_anticipating=True, red_anticipating=False)
        self.assertEqual(sample_board.reward(), -win_value)
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 16, 0],
            [0, 0, 0, 0, 0, 0, 2, 0, 0],
            [0, 0, 15, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=True, red_anticipating=True)
        self.assertEqual(sample_board.reward(), -win_value)

    def test_material(self):
        """
        This verifies that the calculation of material advantage of the player
        to move works as expected.
        """
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 2, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 16, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        self.assertEqual(sample_board.material(), 2)
        sample_board = Board(sample_state_matrix, player_to_move=Player.RED,
                             blue_anticipating=False, red_anticipating=False)
        self.assertEqual(sample_board.material(), -2)

    def test_transition(self):
        """
        This verifies that the next state can be determined given the current
        state and a given (presumably) valid action.
        """
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 2, 0, 0],
            [0, 0, 15, 0, 0, 9, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 16, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        next_board = sample_board.transition(action="2535")
        self.assertEqual(next_board.matrix[3][5], 9)  # Verify piece movement

        sample_state_matrix[3][2] = 16  # Place red flag in front of blue spy
        sample_state_matrix[6][5] = Ranking.BLANK  # Remove former red flag
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        next_board = sample_board.transition(action="2232")
        self.assertTrue(next_board.is_terminal())
        sample_board = Board(sample_state_matrix, player_to_move=Player.RED,
                             blue_anticipating=False, red_anticipating=False)
        next_board = sample_board.transition(action="3222")
        self.assertTrue(next_board.is_terminal())


class TestInfostate(unittest.TestCase):
    """
    This tests the representation of the board as seen by either of the players.
    """

    def test_transition(self):
        """
        This verifies that the infostate representation is configured properly 
        after each move.
        """

        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 17, 1, 0, 0, 2, 30, 0],
            [0, 0, 15, 0, 0, 9, 15, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 16, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        sample_blue_infostate = Infostate.at_start(owner=Player.BLUE,
                                                   board=sample_board)
        next_infostate = sample_blue_infostate.transition(action="4353",
                                                          result=Result.WIN)
        self.assertEqual(next_infostate.matrix[5][3][0], 22)
        self.assertEqual(next_infostate.abstracted_board[5][3].rank_floor, 7)
        next_infostate = sample_blue_infostate.transition(action="1617",
                                                          result=Result.WIN)
        self.assertEqual(next_infostate.matrix[1][6][0], 0)
        self.assertEqual(next_infostate.abstracted_board[1][6].rank_floor, 0)
        next_infostate = sample_blue_infostate.transition(action="1222",
                                                          result=Result.WIN)
        self.assertEqual(next_infostate.abstracted_board[2][2].rank_floor, 2)
        self.assertEqual(next_infostate.abstracted_board[2][2].rank_ceiling, 2)
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 17, 0, 0, 0, 2, 30, 0],
            [0, 0, 15, 0, 0, 9, 15, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 16, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        sample_blue_infostate = Infostate.at_start(owner=Player.BLUE,
                                                   board=sample_board)
        next_infostate = sample_blue_infostate.transition(action="6777",
                                                          result=Result.OCCUPY)
        self.assertEqual(next_infostate.abstracted_board[7][7].rank_floor, 1)
        self.assertTrue(next_infostate.anticipating)
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [16, 0, 17, 0, 0, 0, 2, 30, 0],
            [0, 0, 15, 0, 0, 9, 15, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 16, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.RED,
                             blue_anticipating=False, red_anticipating=False)
        sample_blue_infostate = Infostate.at_start(owner=Player.RED,
                                                   board=sample_board)
        next_infostate = sample_blue_infostate.transition(action="6757",
                                                          result=Result.OCCUPY)
        next_infostate = sample_blue_infostate.transition(action="1000",
                                                          result=Result.OCCUPY)
        self.assertEqual(next_infostate.abstracted_board[0][0].rank_floor, 1)
        self.assertTrue(next_infostate.anticipating)

    def test_flatten(self):
        """
        This confirms whether the infostate is properly flattened on its way to 
        become an infostate string.
        """
        sample_state_matrix = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 17, 1, 0, 0, 2, 30, 0],
            [0, 0, 15, 0, 0, 9, 15, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 23, 0, 29, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 16, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        sample_board = Board(sample_state_matrix, player_to_move=Player.BLUE,
                             blue_anticipating=False, red_anticipating=False)
        sample_blue_infostate = Infostate.at_start(owner=Player.BLUE,
                                                   board=sample_board)
        flattened_infostate = sample_blue_infostate.flatten()
        infostate_string = str(sample_blue_infostate)
        infostate_list = list(map(int, infostate_string.split(" ")))
        self.assertListEqual(
            infostate_list[:-3],
            flattened_infostate)


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

    def test_get_sensible_random_formation(self):
        """
        This ensures that the sampled random formation does not assign the flag
        in the front line.
        """
        piece_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # example piece list

        formation = Player.get_sensible_random_formation(piece_list)
        front_line = formation[:Board.COLUMNS]

        self.assertNotIn(
            Ranking.FLAG, front_line, "FLAG should not be in the front line")


class TestGetSquaresWithinRadius(unittest.TestCase):
    """
    This tests the get_squares_within_radius method of the Board class.
    """

    def test_center_within_bounds(self):
        """
        This checks if the method returns the correct squares within the radius
        when the center is within the bounds of the board.
        """
        board = Board(matrix=[], player_to_move=Player.BLUE,
                      blue_anticipating=False, red_anticipating=False)
        center = (4, 4)
        radius = 2
        expected_squares = [
            (2, 4), (3, 3), (3, 4), (3, 5), (4, 2), (4, 3), (4, 4), (4, 5),
            (4, 6), (5, 3), (5, 4), (5, 5), (6, 4)
        ]
        self.assertEqual(board.get_squares_within_radius(
            center, radius), expected_squares)

    def test_center_at_edge(self):
        """
        This checks if the method returns the correct squares within the radius
        when the center is at the edge of the board.
        """
        board = Board(matrix=[], player_to_move=Player.BLUE,
                      blue_anticipating=False, red_anticipating=False)
        center = (0, 0)
        radius = 2
        expected_squares = [
            (0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)
        ]
        self.assertEqual(board.get_squares_within_radius(
            center, radius), expected_squares)

    def test_center_at_corner(self):
        """
        This checks if the method returns the correct squares within the radius
        when the center is at the corner of the board.
        """
        board = Board(matrix=[], player_to_move=Player.BLUE,
                      blue_anticipating=False, red_anticipating=False)
        center = (7, 8)
        radius = 1
        expected_squares = [
            (6, 8), (7, 7), (7, 8)
        ]
        self.assertEqual(board.get_squares_within_radius(
            center, radius), expected_squares)

    def test_zero_radius(self):
        """
        This checks if the method returns only the center square when the radius
        is zero.
        """
        board = Board(matrix=[], player_to_move=Player.BLUE,
                      blue_anticipating=False, red_anticipating=False)
        center = (4, 4)
        radius = 0
        expected_squares = [(4, 4)]
        self.assertEqual(board.get_squares_within_radius(
            center, radius), expected_squares)

    def test_large_radius(self):
        """
        This checks if the method returns the correct squares within the radius
        when the radius is larger than the board dimensions.
        """
        board = Board(matrix=[], player_to_move=Player.BLUE,
                      blue_anticipating=False, red_anticipating=False)
        center = (4, 4)
        radius = 10
        expected_squares = [
            (i, j) for i in range(Board.ROWS) for j in range(Board.COLUMNS)
        ]
        self.assertEqual(board.get_squares_within_radius(
            center, radius), expected_squares)


if __name__ == '__main__':
    unittest.main()
