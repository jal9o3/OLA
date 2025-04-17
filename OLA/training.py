"""
This contains definitions relevant to the training of an AI for GG.
"""

import random
import csv
import time
import copy

from dataclasses import dataclass
from collections import deque, Counter

import tkinter as tk
from anytree import Node
from anytree.exporter import UniqueDotExporter  # Graphviz has to be installed

from OLA.core import Board, Infostate, Player, BoardPrinter
from OLA.simulation import MatchSimulator
from OLA.constants import Ranking, Result, POV


class MatrixApp:
    def __init__(self, root, matrix):
        self.root = root
        self.matrix = matrix
        self.cells = []
        self.root.wm_attributes('-type', 'dialog')  # Force floating in i3wm
        self.create_widgets()

    def create_widgets(self):
        rows = len(self.matrix)
        cols = len(self.matrix[0])

        # Add row numbers
        for r in range(rows):
            label = tk.Label(self.root, text=str(r))
            label.grid(row=r + 1, column=0)

        # Add column numbers
        for c in range(cols):
            label = tk.Label(self.root, text=str(c))
            label.grid(row=rows + 1, column=c + 1)

        # Create buttons
        for r, row in enumerate(self.matrix):
            for c, value in enumerate(row):
                if value[0] is None:
                    to_show = "   --   "
                elif value[0] == value[1]:
                    to_show = f"   {value[0]}   "
                else:
                    to_show = f"({value[0]}, {value[1]})"
                btn = tk.Button(self.root, text=str(
                    to_show), command=lambda r=r, c=c: self.on_cell_click(r, c))
                btn.grid(row=r + 1, column=c + 1)

    def on_cell_click(self, row, col):
        self.cells.append((row, col))
        if len(self.cells) == 2:
            self.root.destroy()


class Abstraction:
    """
    This replaces the theoretical full history of the game.
    """

    def __init__(self, state: Board, infostate: Infostate):
        self.state = state
        self.infostate = infostate

    def get_state(self) -> Board:
        """
        Returns the current state of the board.

        :return: The current board state.
        """
        return self.state

    def set_state(self, state: Board):
        """
        Sets the state of the board.

        :param state: The new board state to set.
        """
        self.state = state

    def get_infostate(self) -> Infostate:
        """
        Returns the current infostate.

        :return: The current infostate.
        """
        return self.infostate

    def set_infostate(self, infostate: Infostate):
        """
        Sets the infostate.

        :param infostate: The new infostate to set.
        """
        self.infostate = infostate


class TimelessBoard:
    """
    A special "board" for listing all the possible moves that can occur in a 
    game, to be used by the CFRTrainingSimulator in preparing the training data.
    """

    @staticmethod
    def actions():
        """
        This enumerates all the possible actions that can be chosen in every
        game for all the players.
        """

        valid_actions = []  # Initialize return value
        bottom_row_number = leftmost_column_number = 0

        for row in range(Board.ROWS):
            for column in range(Board.COLUMNS):
                # Define change in coordinates per direction (up, down, left,
                # and right)
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for direction in directions:
                    direction_row, direction_column = direction
                    new_row, new_column = (row + direction_row,
                                           column + direction_column)

                    if (bottom_row_number <= new_row < Board.ROWS
                            and leftmost_column_number <= new_column < Board.COLUMNS):
                        valid_actions.append(
                            f"{row}{column}{new_row}{new_column}")

        return valid_actions


@dataclass
class CFRParameters:
    """
    This is for storing the parameters needed by the counterfactual regret
    minimization algorithm.
    """
    abstraction: Abstraction
    current_player: int
    iteration: int
    blue_probability: float
    red_probability: float
    turn_number: int
    depth: int = None
    previous_action: str = None
    previous_result: str = None
    attack_location: tuple[int, int] = None
    actions_filter: 'ActionsFilter' = None
    visualize: bool = False
    data_node: Node = None
    parent_data_node: Node = None
    action_taken: str = None


@dataclass
class Probabilities:
    """
    This is for storing the probabilities of the current player and the opponent 
    for the node.
    """
    opponent_probability: float
    player_probability: float


@dataclass
class Tables:
    """
    A class used to represent tables for storing regrets and strategies.
    Attributes
    ----------
    regret_table : list of float
        A list to store regret values.
    strategy_table : list of float
        A list to store strategy probabilities.
    """
    regret_table: list[float]
    strategy_table: list[float]


@dataclass
class UpdateTablesParams:
    """
    This is for storing the parameters needed to update the regret and strategy
    tables.
    """
    state: Board
    tables: Tables
    profile: list[float]
    utilities: list[float]
    node_utility: float
    probabilities: Probabilities
    infostate: Infostate


@dataclass
class DirectionFilter:
    """
    This is for defining which directions of movement should be evaluated,
    intended to be used with the ActionsFilter class.
    """

    forward: bool = True
    back: bool = True
    left: bool = True
    right: bool = True


class ActionsFilter:
    """
    This is for defining the criteria for which moves in a given game state
    should be evaluated.
    """

    def __init__(self, state: Board, directions: DirectionFilter,
                 square_whitelist: list[tuple[int, int]]):
        self.state = state
        self.directions = directions
        self.square_whitelist = square_whitelist

    def filter(self):
        """
        This method filters the actions available in the current game state.
        """
        actions = self.state.actions()
        filtered_actions = []
        for action in actions:
            if self._to_include(action):
                filtered_actions.append(action)

        return filtered_actions

    def _to_include(self, action: str):
        """
        This method checks if an action is valid.
        """
        is_included = False  # Initialize the return value
        # If the action's starting or destination square is in the whitelist
        if ((int(action[0]), int(action[1])) in self.square_whitelist
                or (int(action[2]), int(action[3])) in self.square_whitelist):
            is_included = True
        else:
            return False

        # Blue's forward moves are those that increase the row number
        if (self.state.player_to_move == Player.BLUE
                and int(action[0]) < int(action[2]) and self.directions.forward):
            is_included = True
        elif (self.state.player_to_move == Player.BLUE
                and int(action[0]) < int(action[2]) and not self.directions.forward):
            is_included = False

        if (self.state.player_to_move == Player.BLUE
                and int(action[0]) > int(action[2]) and self.directions.back):
            is_included = True
        elif (self.state.player_to_move == Player.BLUE
                and int(action[0]) > int(action[2]) and not self.directions.back):
            is_included = False

        # Blue's right moves are those that decrease the column number
        if (self.state.player_to_move == Player.BLUE
                and int(action[1]) > int(action[3]) and self.directions.right):
            is_included = True
        elif (self.state.player_to_move == Player.BLUE
                and int(action[1]) > int(action[3]) and not self.directions.right):
            is_included = False

        if (self.state.player_to_move == Player.BLUE
                and int(action[1]) < int(action[3]) and self.directions.left):
            is_included = True
        elif (self.state.player_to_move == Player.BLUE
                and int(action[1]) < int(action[3]) and not self.directions.left):
            is_included = False

        # Flip the logic for red player
        if (self.state.player_to_move == Player.RED
                and int(action[0]) > int(action[2]) and self.directions.forward):
            is_included = True
        elif (self.state.player_to_move == Player.RED
                and int(action[0]) > int(action[2]) and not self.directions.forward):
            is_included = False

        if (self.state.player_to_move == Player.RED
                and int(action[0]) < int(action[2]) and self.directions.back):
            is_included = True
        elif (self.state.player_to_move == Player.RED
                and int(action[0]) < int(action[2]) and not self.directions.back):
            is_included = False

        if (self.state.player_to_move == Player.RED
                and int(action[1]) < int(action[3]) and self.directions.right):
            is_included = True
        elif (self.state.player_to_move == Player.RED
                and int(action[1]) < int(action[3]) and not self.directions.right):
            is_included = False

        if (self.state.player_to_move == Player.RED and self.directions.left
                and int(action[1]) > int(action[3])):
            is_included = True
        elif (self.state.player_to_move == Player.RED
                and int(action[1]) > int(action[3]) and not self.directions.left):
            is_included = False
        return is_included


class CFRTrainer:
    """
    This is responsible for generating regret and strategy tables using the
    counterfactual regret minimization algorithm.
    """

    def __init__(self):
        self.regret_tables = {}
        self.strategy_tables = {}
        self.profiles = {}

    @staticmethod
    def _initialize_utilities(state: Board):
        node_utility = 0
        utilities = [0.0 for action in state.actions()]

        return node_utility, utilities

    def _get_tables(self, state: Board, infostate: Infostate):
        if str(infostate) not in self.regret_tables:
            regret_table = [0.0 for action in state.actions()]
        else:
            regret_table = self.regret_tables[str(infostate)]

        if str(infostate) not in self.strategy_tables:
            strategy_table = [0.0 for action in state.actions()]
        else:
            strategy_table = self.strategy_tables[str(infostate)]

        if str(infostate) not in self.profiles:
            profile = [1.0/len(state.actions()) for action in state.actions()]
        else:
            profile = self.profiles[str(infostate)]

        return regret_table, strategy_table, profile

    @staticmethod
    def _get_next(state: Board, infostate: Infostate, action: str):
        next_state = state.transition(action=action)
        result = state.classify_action_result(action=action,
                                              new_board=next_state)
        next_infostate = infostate.transition(action=action, result=result)

        return next_state, next_infostate

    @staticmethod
    def _update_probabilities(state: Board, profile: list[float],
                              blue_probability: float, red_probability: float,
                              action_index: int):
        new_blue_probability = blue_probability
        new_red_probability = red_probability  # Initialize new probabilities
        if state.player_to_move == Player.BLUE:
            new_blue_probability = profile[action_index]*blue_probability
        elif state.player_to_move == Player.RED:
            new_red_probability = profile[action_index]*red_probability

        return new_blue_probability, new_red_probability

    @staticmethod
    def _probabilities(current_player: int, blue_probability: float,
                       red_probability: float):
        opponent = Player.RED if current_player == Player.BLUE else Player.BLUE
        player_probability = (blue_probability if current_player == Player.BLUE
                              else red_probability)
        opponent_probability = (blue_probability if opponent == Player.BLUE
                                else red_probability)

        return player_probability, opponent_probability

    @staticmethod
    def _regret_match(state: Board, regret_table: list[float]):
        # Calculate next profile using nonnegative regret matching
        next_profile = [0.0 for _ in state.actions()]

        if all(r <= 0 for r in regret_table):
            next_profile = [1 / len(state.actions()) for _ in state.actions()]
        else:
            positive_regret_sum = sum(r for r in regret_table if r > 0)
            for r, regret in enumerate(regret_table):
                if regret > 0:
                    next_profile[r] = regret / positive_regret_sum

        return next_profile

    def _cfr_children(self, parameters: CFRParameters, profile: list[float], utilities: list[float],
                      node_utility: float):
        state, infostate = parameters.abstraction.state, parameters.abstraction.infostate
        for a, action in enumerate(state.actions()):
            next_state, next_infostate = CFRTrainer._get_next(
                state=state, infostate=infostate, action=action)

            new_blue_probability, new_red_probability = (
                CFRTrainer._update_probabilities(
                    state=state, profile=profile, blue_probability=parameters.blue_probability,
                    red_probability=parameters.red_probability, action_index=a))
            new_parameters = CFRParameters(abstraction=Abstraction(
                state=next_state, infostate=next_infostate),
                current_player=parameters.current_player, iteration=parameters.iteration,
                blue_probability=new_blue_probability, red_probability=new_red_probability)
            utilities[a] = -self.cfr(params=new_parameters)

            node_utility += profile[a]*utilities[a]

        return node_utility

    def cfr(self, params: CFRParameters):
        """
        This is the recursive algorithm for calculating counterfactual regret.
        """
        abstraction, current_player, blue_probability, red_probability = (
            params.abstraction, params.current_player, params.blue_probability,
            params.red_probability
        )

        if abstraction.state.is_terminal():
            return self._terminal_state_utility(abstraction.state, current_player)

        node_utility, utilities = CFRTrainer._initialize_utilities(
            state=abstraction.state)
        regret_table, strategy_table, profile = self._get_tables(
            state=abstraction.state, infostate=abstraction.infostate)
        player_probability, opponent_probability = CFRTrainer._probabilities(
            current_player=current_player, blue_probability=blue_probability,
            red_probability=red_probability)

        node_utility = self._cfr_children(parameters=params, profile=profile,
                                          utilities=utilities, node_utility=node_utility)

        if abstraction.state.player_to_move == current_player:
            self._update_tables(
                UpdateTablesParams(
                    state=abstraction.state,
                    tables=Tables(
                        regret_table=regret_table,
                        strategy_table=strategy_table), profile=profile, utilities=utilities,
                    node_utility=node_utility,
                    probabilities=Probabilities(
                        opponent_probability=opponent_probability,
                        player_probability=player_probability), infostate=abstraction.infostate))

        return node_utility

    def _terminal_state_utility(self, state: Board, current_player: int):
        if state.player_to_move == current_player:
            return state.reward()

        return -state.reward()

    def _update_tables(self, params: UpdateTablesParams):
        for a in range(len(params.state.actions())):
            params.tables.regret_table[a] += params.probabilities.opponent_probability * \
                (params.utilities[a] - params.node_utility)
            params.tables.strategy_table[a] += params.probabilities.player_probability * \
                params.profile[a]

        self.regret_tables[str(params.infostate)] = params.tables.regret_table
        self.strategy_tables[str(params.infostate)
                             ] = params.tables.strategy_table

        next_profile = CFRTrainer._regret_match(
            state=params.state, regret_table=params.tables.regret_table)
        self.profiles[str(params.infostate)] = next_profile

    def solve(self, abstraction: Abstraction, turn_number: int,
              iterations: int = 100000):
        """
        This runs the counterfactual regret minimization algorithm to produce
        the tables needed by the AI.
        """
        for i in range(iterations):
            for player in [Player.BLUE, Player.RED]:
                arguments = CFRParameters(abstraction=abstraction, current_player=player,
                                          iteration=i, blue_probability=1, red_probability=1,
                                          turn_number=turn_number)
                self.cfr(params=arguments)


class DepthLimitedCFRTrainer(CFRTrainer):
    """
    This implements a modified CFR that recurses only to a specified depth and
    uses heuristic reward evaluations.
    """

    def __init__(self):
        super().__init__()
        self.vanilla_cfr = CFRTrainer()  # For accessing original implementation
        self.memo_cache = {}

    @staticmethod
    def _get_actions_filter(arbiter_board: Board, previous_action: str, previous_result: str,
                            attack_location: tuple[int, int]):
        reduced_branching, radius = 0, 1
        while reduced_branching <= 0:
            radius += 1
            if previous_result in [Result.WIN, Result.LOSS]:
                center = attack_location
            elif attack_location is None:
                center = (int(previous_action[0]), int(previous_action[1]))
            else:
                return None

            whitelist = arbiter_board.get_squares_within_radius(
                center=center, radius=radius)
            actions_filter = ActionsFilter(
                state=arbiter_board, directions=DirectionFilter(), square_whitelist=whitelist)
            reduced_branching = len(actions_filter.filter())
        return actions_filter

    def _cfr_children(self, parameters: CFRParameters, profile: list[float], utilities: list[float],
                      node_utility: float
                      ):
        state, infostate = parameters.abstraction.state, parameters.abstraction.infostate

        actions_filter = None
        # Get new actions filter
        if (parameters.previous_action is not None
            and parameters.previous_result is not None
                and parameters.turn_number not in [1, 2]):
            actions_filter = DepthLimitedCFRTrainer._get_actions_filter(
                arbiter_board=state, previous_action=parameters.previous_action,
                previous_result=parameters.previous_result,
                attack_location=parameters.attack_location
            )
        elif (parameters.previous_action is not None
              and parameters.previous_result is not None
                and parameters.turn_number in [1, 2]):
            actions_filter = ActionsFilter(state=state, directions=DirectionFilter(
                back=False, right=False, left=False),
                square_whitelist=[(x, y) for y in range(Board.COLUMNS)
                                  for x in range(Board.ROWS)])

        if actions_filter is not None:
            filtered_actions = actions_filter.filter()
        else:
            filtered_actions = None

        for a, action in enumerate(state.actions()):
            if filtered_actions is not None and action not in filtered_actions:
                utilities[a] = 0
                continue

            new_state = state.transition(action)
            result = state.classify_action_result(
                action, new_state)

            if result in [Result.WIN, Result.LOSS]:
                attack_location = (int(action[2]), int(action[3]))
            else:
                attack_location = None

            next_state, next_infostate = CFRTrainer._get_next(
                state=state, infostate=infostate, action=action)

            new_blue_probability, new_red_probability = (
                CFRTrainer._update_probabilities(
                    state=state, profile=profile, blue_probability=parameters.blue_probability,
                    red_probability=parameters.red_probability, action_index=a))

            arguments = CFRParameters(abstraction=Abstraction(
                state=next_state, infostate=next_infostate),
                current_player=parameters.current_player, iteration=parameters.iteration,
                blue_probability=new_blue_probability, red_probability=new_red_probability,
                depth=parameters.depth-1, actions_filter=actions_filter,
                previous_action=action, previous_result=result, attack_location=attack_location,
                turn_number=parameters.turn_number + 1, visualize=parameters.visualize,
                parent_data_node=parameters.parent_data_node, action_taken=action)

            utilities[a] = -self.cfr(params=arguments)

            node_utility += profile[a]*utilities[a]

        return node_utility, utilities

    def cfr(self, params: CFRParameters):
        """
        This is the recursive algorithm for calculating counterfactual regret.
        """
        abstraction, current_player, blue_probability, red_probability, depth = (
            params.abstraction, params.current_player, params.blue_probability,
            params.red_probability, params.depth
        )

        key = (abstraction.infostate, depth, abstraction.state.player_to_move)
        if params.iteration > 1 and key in self.memo_cache:
            return self.memo_cache[key]

        player_probability, opponent_probability = CFRTrainer._probabilities(
            current_player=abstraction.state.player_to_move, blue_probability=blue_probability,
            red_probability=red_probability)

        if params.visualize and params.parent_data_node is not None:
            data_node = Node(
                f"Utility: Unknown\n{opponent_probability*100:.2f}%",
                parent=params.parent_data_node
            )
            params.data_node = data_node
        elif params.visualize and params.parent_data_node is None:
            data_node = Node(
                f"Utility: Unknown\n{opponent_probability*100:.2f}%"
            )
            params.data_node = data_node

        if abstraction.state.is_terminal():
            node_utility = abstraction.state.reward()

            if (params.visualize and params.data_node is not None
                    and params.action_taken is not None):
                params.data_node.name = (
                    f"{params.action_taken}\n"
                    f"Utility: {node_utility:.2f}\n{opponent_probability*100:.2f}%")

            self.memo_cache[key] = node_utility
            return node_utility

        if depth == 0:
            node_utility = abstraction.state.evaluation()

            if params.visualize and params.data_node is not None:
                params.data_node.name = (
                    f"{params.action_taken}\n"
                    f"Utility: {node_utility:.2f}\n{opponent_probability*100:.2f}%")

            self.memo_cache[key] = node_utility
            return node_utility

        node_utility, utilities = CFRTrainer._initialize_utilities(
            state=abstraction.state)

        regret_table, strategy_table, profile = self._get_tables(
            state=abstraction.state, infostate=abstraction.infostate)

        new_params = copy.deepcopy(params)
        if params.visualize and params.data_node is not None:
            new_params.parent_data_node = data_node

        node_utility, utilities = self._cfr_children(parameters=new_params, profile=profile,
                                                     utilities=utilities, node_utility=node_utility)

        if abstraction.state.player_to_move == current_player:
            self._update_tables(
                UpdateTablesParams(
                    state=abstraction.state,
                    tables=Tables(
                        regret_table=regret_table,
                        strategy_table=strategy_table), profile=profile, utilities=utilities,
                    node_utility=node_utility,
                    probabilities=Probabilities(
                        opponent_probability=opponent_probability,
                        player_probability=player_probability), infostate=abstraction.infostate))

        if params.visualize and params.data_node is not None:
            params.data_node.name = f"Utility: {node_utility:.2f}\n{opponent_probability*100:.2f}%"

            if params.action_taken is not None:
                params.data_node.name = f"{params.action_taken}\n" + \
                    params.data_node.name

        return node_utility

    def _depth_limited_utility(self, state: Board, current_player: int):
        if state.player_to_move == current_player:
            return state.evaluation()
        return -state.evaluation()

    def solve(self, abstraction: Abstraction, turn_number: int,
              iterations: int = 10, depth: int = 2,
              actions_filter: ActionsFilter = None, previous_action: str = None,
              previous_result: str = None, attack_location: tuple[int, int] = None):
        """
        This runs the counterfactual regret minimization algorithm to produce
        the tables needed by the AI.
        """

        visualize = False

        # To avoid running out of memory
        self.memo_cache = {}

        for i in range(iterations):
            depth = 2

            print(f"{i} ", end='', flush=True)
            for player in [Player.BLUE, Player.RED]:

                if (i == iterations - 1
                        and abstraction.state.player_to_move == player):
                    # visualize = True
                    pass

                arguments = CFRParameters(abstraction=abstraction, current_player=player,
                                          iteration=i, blue_probability=1, red_probability=1,
                                          depth=depth, actions_filter=actions_filter,
                                          turn_number=turn_number, previous_action=previous_action,
                                          previous_result=previous_result,
                                          attack_location=attack_location,
                                          visualize=visualize)

                self.cfr(params=arguments)

                if (visualize and i == iterations - 1
                        and abstraction.state.player_to_move == player):
                    UniqueDotExporter(arguments.data_node).to_picture(
                        "/home/romlor/Desktop/cfr.png")

        print()


class RepetitionDetector:
    def __init__(self, window_size=6, max_repeats=2):
        self.history = deque(maxlen=100)  # full move history (for reference)
        self.recent_sequences = Counter()
        self.window_size = window_size
        self.max_repeats = max_repeats

    def add_move(self, move):
        self.history.append(move)
        if len(self.history) >= self.window_size:
            recent_chunk = tuple(list(self.history)[-self.window_size:])
            self.recent_sequences[recent_chunk] += 1
            return self.recent_sequences[recent_chunk] >= self.max_repeats
        return False

    def reset(self):
        self.history.clear()
        self.recent_sequences.clear()


class CFRTrainingSimulator(MatchSimulator):
    """
    This handles the game simulations for generating the AI's training data. The
    controller is assumed to be the counterfactual regret minimization
    algorithm.
    """

    def __init__(self, formations: list[list[int]], controllers: list[int],
                 save_data: bool, pov: int):
        super().__init__(formations, controllers, save_data, pov)
        self.controllers = None

    @staticmethod
    def _distill_strategy(raw_strategy: list[float]):
        positive_sum = 0  # Initialize sum of positive probabilities
        # Initialize list for the normalized strategy
        normalized_strategy = [0.0 for i in range(len(raw_strategy))]
        for probability in raw_strategy:
            if probability > 0:
                positive_sum += probability

        for i, probability in enumerate(raw_strategy):
            if probability > 0:
                normalized_strategy[i] = probability/positive_sum

        return normalized_strategy

    def get_cfr_input(self, abstraction: Abstraction, turn_number: int,
                      actions_filter: ActionsFilter = None, previous_action: str = None,
                      previous_result: str = None, attack_location: tuple[int, int] = None,
                      trainer: DepthLimitedCFRTrainer = None):
        """This is for obtaining the CFR controller's chosen action"""

        valid_actions = abstraction.state.actions()
        action = ""

        if trainer is None:
            trainer = DepthLimitedCFRTrainer()

        trainer.solve(abstraction, iterations=11, actions_filter=actions_filter,
                      turn_number=turn_number, previous_action=previous_action,
                      previous_result=previous_result, attack_location=attack_location)

        strategy = CFRTrainingSimulator._distill_strategy(
            trainer.strategy_tables[str(abstraction.infostate)])

        # Set the bottom_k lowest probabilities to 0
        bottom_k = 3
        for _ in range(bottom_k):
            threshold = min(strategy)
            for i, probability in enumerate(strategy):
                if probability <= threshold:
                    strategy[i] = 0

        normalizing_sum = sum(strategy)
        if normalizing_sum > 0:
            strategy = [p / normalizing_sum for p in strategy]
        else:
            # Reset options if all evaluated actions seem bad
            strategy = [1 / len(valid_actions) for _ in valid_actions]

        if actions_filter is None:
            # Find all actions with the maximum probability
            max_probability = max(strategy)
            max_indices = [i for i, p in enumerate(
                strategy) if p == max_probability]
            # Choose randomly among them
            action = valid_actions[random.choice(max_indices)]
        else:
            filtered_actions = actions_filter.filter()
            filtered_strategy = []

            for a, action in enumerate(valid_actions):
                if action in filtered_actions:
                    filtered_strategy.append(strategy[a])

            normalizing_sum = sum(filtered_strategy)
            if normalizing_sum > 0:
                filtered_strategy = [
                    p / normalizing_sum for p in filtered_strategy]
            else:
                # Reset options if all evaluated actions seem bad
                filtered_actions, filtered_strategy = valid_actions, strategy

            # Find all actions with the maximum probability
            max_probability = max(filtered_strategy)
            max_indices = [i for i, p in enumerate(
                filtered_strategy) if p == max_probability]
            # Choose randomly among them
            action = filtered_actions[random.choice(max_indices)]

        return action, trainer, strategy[valid_actions.index(action)]

    @staticmethod
    def _get_actions_filter(arbiter_board, previous_action, previous_result, attack_location):
        reduced_branching, radius = 0, 1
        while reduced_branching <= 0:
            radius += 1
            if previous_result in [Result.WIN, Result.LOSS]:
                center = attack_location
            elif attack_location is None:
                center = (int(previous_action[0]), int(previous_action[1]))
            else:
                return None

            whitelist = arbiter_board.get_squares_within_radius(
                center=center, radius=radius)
            actions_filter = ActionsFilter(
                state=arbiter_board, directions=DirectionFilter(), square_whitelist=whitelist)
            reduced_branching = len(actions_filter.filter())
        return actions_filter

    def _initialize_arbiter_board(self):
        arbiter_board = Board(self.setup_arbiter_matrix(),
                              player_to_move=Player.BLUE,
                              blue_anticipating=False, red_anticipating=False)
        if self.save_data:
            self.game_history.append(arbiter_board.matrix)
        return arbiter_board

    def _process_action(self, arbiter_board: Board, action: str):
        new_arbiter_board = arbiter_board.transition(action)
        result = arbiter_board.classify_action_result(
            action, new_arbiter_board)
        if result in [Result.WIN, Result.LOSS]:
            attack_location = (int(action[2]), int(action[3]))
        else:
            attack_location = None
        return new_arbiter_board, result, attack_location

    @staticmethod
    def _save_strategy_to_csv(current_abstraction: Abstraction,
                              trainer: DepthLimitedCFRTrainer):
        # Map the strategy to all possible actions
        fullgame_actions = TimelessBoard.actions()
        strategy = CFRTrainingSimulator._distill_strategy(
            raw_strategy=trainer.strategy_tables[str(current_abstraction.infostate)])
        # Initialize the full size strategy
        full_strategy = [0.0 for a in range(len(fullgame_actions))]
        for action in current_abstraction.state.actions():
            full_strategy[fullgame_actions.index(action)] = strategy[
                current_abstraction.state.actions().index(action)]
        # Store the infostate string with the corresponding strategy in a CSV file
        with open("training_data.csv", "a", encoding="utf-8") as training_data:
            writer = csv.writer(training_data)
            # Split the infostate string
            infostate_split = list(
                map(int, str(current_abstraction.infostate).split(" ")))
            writer.writerow(infostate_split + full_strategy)

    def start(self, iterations: int = 1, target: int = None):
        """
        This method simulates a GG match generating training data, using the
        counterfactual regret minimization algorithm.
        """
        trainer = None
        start = time.time()
        _ = iterations  # Not used in this subclass
        sampled = 0  # Initialize data sample count

        while target is not None and sampled < target:
            self.blue_formation = list(
                Player.get_sensible_random_formation(
                    piece_list=Ranking.SORTED_FORMATION)
            )
            self.red_formation = self._place_in_red_range(list(
                Player.get_sensible_random_formation(
                    piece_list=Ranking.SORTED_FORMATION))
            )

            arbiter_board = self._initialize_arbiter_board()
            blue_infostate, red_infostate = MatchSimulator._starting_infostates(
                arbiter_board)

            action, result, previous_action, previous_result, attack_location = (
                "", "", None, None, None)  # Initialize needed values
            trainer = None
            turn_number = 1

            detector = RepetitionDetector()  # For detecting repetition of moves

            while not arbiter_board.is_terminal():
                MatchSimulator._print_game_status(turn_number, arbiter_board, infostates=[
                    blue_infostate, red_infostate],
                    pov=self.pov)

                print(f"Naive Evaluation: {arbiter_board.evaluation()}")

                action = ""  # Initialize variable for storing chosen action
                current_infostate = (blue_infostate if arbiter_board.player_to_move == Player.BLUE
                                     else red_infostate)
                current_abstraction = Abstraction(
                    state=arbiter_board, infostate=current_infostate)

                # For the first turns of each player, choose a forward move
                if turn_number in [1, 2]:
                    actions_filter = ActionsFilter(state=arbiter_board, directions=DirectionFilter(
                        back=False, right=False, left=False),
                        square_whitelist=[(x, y) for y in range(Board.COLUMNS)
                                          for x in range(Board.ROWS)])
                else:
                    actions_filter = CFRTrainingSimulator._get_actions_filter(
                        arbiter_board, previous_action, previous_result, attack_location)

                action, trainer, chance = self.get_cfr_input(abstraction=current_abstraction,
                                                             actions_filter=actions_filter,
                                                             turn_number=turn_number,
                                                             previous_action=previous_action,
                                                             previous_result=previous_result,
                                                             attack_location=attack_location,
                                                             trainer=trainer)

                print(f"Chosen Move: {action}")
                print(f"{chance*100:.5f}% chance")

                previous_action = action  # Store for the next iteration

                arbiter_board, result, attack_location = self._process_action(
                    arbiter_board, action)

                previous_result = result  # Store for the next iteration

                blue_infostate, red_infostate = MatchSimulator._update_infostates(
                    blue_infostate, red_infostate, action=action, result=result
                )

                turn_number += 1
                sampled += 1
                print(f"Sampled: {sampled}/{target}")

                self._save_strategy_to_csv(current_abstraction=current_abstraction,
                                           trainer=trainer)

                if detector.add_move(action):
                    print("De facto draw by repetition")
                    break

            MatchSimulator._print_result(arbiter_board)

        end = time.time()
        print(f"{(end - start)/60/60:.2f} hours elapsed.")
