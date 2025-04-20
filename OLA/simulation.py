"""
This contains the logic for simulating a GG match.
"""

import random

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from OLA.constants import Ranking, POV, Controller
from OLA.helpers import get_blank_matrix
from OLA.core import Player, Board, Infostate


class MatchSimulator:
    """
    This class handles the simulation of a GG match.
    """

    def __init__(self, formations: list[list[int]], controllers: list[int],
                 save_data: bool, pov: int):
        """
        The controllers parameter sets whether a human or an algorithm chooses
        the moves for either or both sides of the simulated match (see constant
        definitions in the Controller class).
        """
        if formations[0] is not None:
            self.blue_formation = formations[0]
        else:
            self.blue_formation = None
        if formations[1] is not None:
            self.red_formation = self._place_in_red_range(formations[1])
        else:
            self.red_formation = None
        self.controllers = controllers
        self.player_one_color = random.choice([Player.BLUE, Player.RED])
        self.player_two_color = Player.RED if (
            self.player_one_color == Player.BLUE) else Player.BLUE
        self.save_data = save_data
        self.game_history = []
        self.pov = pov

    @staticmethod
    def _place_in_red_range(formation: list[int]):
        """
        This is to ensure that the red player's pieces are between 16 and 30
        (see Ranking class for details).
        """

        for i, entry in enumerate(formation):
            if entry > Ranking.BLANK:
                formation[i] += Ranking.SPY

        return formation

    @staticmethod
    def _prepare_empty_matrices():
        """
        This helper method prepares a blank starting matrix for each of the two
        players.
        """
        blue_player_matrix = get_blank_matrix(rows=Board.ROWS,
                                              columns=Board.COLUMNS)
        red_player_matrix = get_blank_matrix(rows=Board.ROWS,
                                             columns=Board.COLUMNS)

        return blue_player_matrix, red_player_matrix

    @staticmethod
    def _place_formation_on_matrix(formation: list[int],
                                   matrix: list[list[int]]):
        """
        The formation is placed on the first three rows of the player's side
        of the board. The formation list must enumerate from the furthermost
        row (from the player's perspective) to the nearest, from left to right.
        """
        i = 0
        for row in range(Board.ROWS-3, Board.ROWS):
            for column in range(Board.COLUMNS):
                if i < len(formation):
                    matrix[row][column] = formation[i]
                    i += 1

        return matrix

    @staticmethod
    def _flip_matrix(matrix: list[list[int]]):
        """
        This helper method is for placing the blue pieces in their starting
        positions from (0,0) to (2,8).
        """
        # Flip the matrix upside down
        matrix = matrix[::-1]
        # Flip each blue board row left to right
        matrix = [row[::-1] for row in matrix]

        return matrix

    @staticmethod
    def _combine_player_matrices(blue_player_matrix: list[list[int]],
                                 red_player_matrix: list[list[int]]):
        """
        This helper method is for joining the blue and red starting matrices
        into one matrix for the arbiter.
        """
        combined_matrix = [
            [blue_player_matrix[i][j] + red_player_matrix[i][j] for j in range(
                Board.COLUMNS)] for i in range(Board.ROWS)
        ]

        return combined_matrix

    def setup_arbiter_matrix(self):
        """
        This instance method takes the provided blue and red formations and
        returns a matrix for the arbiter that represents the initial game state.
        """
        blue_player_matrix, red_player_matrix = (
            MatchSimulator._prepare_empty_matrices()
        )
        blue_player_matrix = MatchSimulator._place_formation_on_matrix(
            self.blue_formation, blue_player_matrix)
        # The blue player's pieces must initially occupy from (0,0) to (2,8)
        blue_player_matrix = MatchSimulator._flip_matrix(blue_player_matrix)
        red_player_matrix = MatchSimulator._place_formation_on_matrix(
            self.red_formation, red_player_matrix)
        arbiter_matrix = MatchSimulator._combine_player_matrices(
            blue_player_matrix, red_player_matrix)

        return arbiter_matrix

    @staticmethod
    def _print_game_status(turn_number: int, arbiter_board: Board,
                           infostates: list[Infostate], pov: int):

        blue_infostate, red_infostate = infostates[0], infostates[1]
        print(f"Turn Number: {turn_number}")
        if pov == POV.WORLD:
            arbiter_board.print_state(POV.WORLD, with_color=True)
        elif pov == POV.BLUE:
            blue_infostate.print_state()
        elif pov == POV.RED:
            red_infostate.print_state()

        print(f"Player to move: {arbiter_board.player_to_move}")

    def get_current_controller(self, board: Board):
        """
        This determines the source of moves of the MatchSimulator.
        """
        current_controller = None  # Initialize return value
        if board.player_to_move == self.player_one_color:
            current_controller = self.controllers[0]
        elif board.player_to_move == self.player_two_color:
            current_controller = self.controllers[1]

        return current_controller

    @staticmethod
    def _starting_infostates(arbiter_board: Board):
        blue_infostate = Infostate.at_start(owner=Player.BLUE,
                                            board=arbiter_board)
        red_infostate = Infostate.at_start(owner=Player.RED,
                                           board=arbiter_board)

        return blue_infostate, red_infostate

    def manage_pov_switching(self, arbiter_board: Board):
        """
        This is for setting the POV when one of the controllers is human.
        """
        # Assume that only one of the controllers is human
        if (self.get_current_controller(arbiter_board) == Controller.HUMAN
                and arbiter_board.player_to_move == Player.BLUE):
            self.pov = POV.BLUE
        elif (self.get_current_controller(arbiter_board) == Controller.HUMAN
                and arbiter_board.player_to_move == Player.RED):
            self.pov = POV.RED
        elif Controller.HUMAN in self.controllers:
            self.pov = None

    def get_controller_input(self, arbiter_board: Board):
        """
        This is for obtaining the controller's chosen action, be it human or
        bot.
        """
        action = ""  # Initialize variable for storing chosen action
        valid_actions = arbiter_board.actions()
        if self.get_current_controller(arbiter_board) == Controller.RANDOM:
            action = random.choice(valid_actions)
        elif self.get_current_controller(arbiter_board) == Controller.HUMAN:
            while action not in valid_actions:
                action = input("Choose a move: ")

        return action

    @staticmethod
    def _update_infostates(blue_infostate: Infostate, red_infostate: Infostate,
                           action: str, result: str):
        blue_infostate = blue_infostate.transition(action, result=result)
        red_infostate = red_infostate.transition(action, result=result)

        return blue_infostate, red_infostate

    @staticmethod
    def _get_match_result(arbiter_board: Board):
        win_value = 1000000
        result = None  # Initialize return value
        if ((arbiter_board.reward() == win_value
                and arbiter_board.player_to_move == Player.BLUE)
                or (arbiter_board.reward() == -win_value
                    and arbiter_board.player_to_move == Player.RED)):
            result = Player.BLUE
        elif ((arbiter_board.reward() == win_value
              and arbiter_board.player_to_move == Player.RED)
              or (arbiter_board.reward() == -win_value
              and arbiter_board.player_to_move == Player.BLUE)):
            result = Player.RED
        elif arbiter_board.reward() == 0:
            result = Player.ARBITER

        return result

    @staticmethod
    def _print_result(arbiter_board: Board):
        result = MatchSimulator._get_match_result(arbiter_board)
        if result == Player.BLUE:
            print("\n[VICTORY FOR BLUE]\n")
        elif result == Player.RED:
            print("\n[VICTORY FOR RED]\n")
        elif result == Player.ARBITER:
            print("\n[DRAW]\n")

    def start(self, iterations: int = 1, target: int = None):
        """
        This method simulates a GG match in the terminal, either taking input
        from humans or choosing moves based on an algorithm or even both.
        """
        _ = target  # Placeholder for use in CFRTrainingSimulator subclass
        branching_lists = []
        for _ in range(iterations):
            branching_list = []  # List for branching at every turn
            arbiter_board = Board(self.setup_arbiter_matrix(),
                                  player_to_move=Player.BLUE,
                                  blue_anticipating=False, red_anticipating=False)
            if self.save_data:
                self.game_history.append(arbiter_board.matrix)

            blue_infostate, red_infostate = MatchSimulator._starting_infostates(
                arbiter_board)

            turn_number = 1
            while not arbiter_board.is_terminal():
                self.manage_pov_switching(arbiter_board)

                MatchSimulator._print_game_status(turn_number, arbiter_board,
                                                  infostates=[
                                                      blue_infostate,
                                                      red_infostate],
                                                  pov=self.pov)
                valid_actions = arbiter_board.actions()
                branching_list.append((turn_number, len(valid_actions)))

                action = ""  # Initialize variable for storing chosen action
                action = self.get_controller_input(arbiter_board)
                print(f"Chosen Move: {action}")
                if self.save_data:
                    self.game_history.append(action)

                new_arbiter_board = arbiter_board.transition(action)
                result = arbiter_board.classify_action_result(action,
                                                              new_arbiter_board)
                blue_infostate, red_infostate = MatchSimulator._update_infostates(
                    blue_infostate, red_infostate, action=action, result=result
                )
                arbiter_board = new_arbiter_board
                turn_number += 1
            branching_lists.append(branching_list)

            MatchSimulator._print_result(arbiter_board)

        for line_data in branching_lists:
            x, y = zip(*line_data)
            plt.scatter(x, y)

        plt.xlabel('Turn Number')
        plt.ylabel('Number of Possible Actions')
        plt.title('Number of Possible Actions Per Turn In 5 Random Games')
        plt.grid(True)

        plt.gca().xaxis.set_major_locator(MultipleLocator(40))  # X-axis interval
        plt.gca().yaxis.set_major_locator(MultipleLocator(5))  # y-axis every 1 unit

        # Lock x-limits to data range
        # all_x = [x for group in branching_lists for x, _ in group]
        # plt.xlim(min(all_x), max(all_x))

        plt.show()
