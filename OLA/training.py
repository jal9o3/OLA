"""
This contains definitions relevant to the training of an AI for GG.
"""

import random
import csv
import copy
import time

from dataclasses import dataclass

from OLA.core import Board, Infostate, Player
from OLA.simulation import MatchSimulator
from OLA.constants import Ranking, Result


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
    depth: int = None
    actions_filter: 'ActionsFilter' = None


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

    nodes_visited = 0  # Counter for visited nodes

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

    def move_ordering(self):
        """
        This method is for ordering the moves in the current game state, for
        use with game tree pruning.
        """
        bottom_row_number = leftmost_column_number = 0
        actions = self.state.actions()
        updated_actions = copy.deepcopy(actions)  # To protect the iterable
        ordered_actions = []

        # Get attacking moves first
        for action in actions:
            if (self.state.not_allied_piece(self.state.matrix[int(action[2])][int(action[3])])
                    and self.state.matrix[int(action[2])][int(action[3])] != Ranking.BLANK):
                ordered_actions.append(action)
                updated_actions.remove(action)
        actions = copy.deepcopy(updated_actions)

        # Get the threatening moves
        for action in actions:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            move_direction = (int(action[2])-int(action[0]),
                              int(action[3])-int(action[1]))
            reversed_direction = (-move_direction[0], -move_direction[1])
            dest_row, dest_col = int(action[2]), int(action[3])
            for direction in directions:
                if (direction != reversed_direction
                    and bottom_row_number <= dest_row + direction[0] < Board.ROWS
                    and leftmost_column_number <= dest_col + direction[1] < Board.COLUMNS
                    and self.state.not_allied_piece(self.state.matrix[
                        dest_row + direction[0]][dest_col + direction[1]])
                    and self.state.matrix[dest_row + direction[0]][
                        dest_col + direction[1]] != Ranking.BLANK):
                    ordered_actions.append(action)
                    updated_actions.remove(action)
                    break  # One threatened target is enough

        actions = copy.deepcopy(updated_actions)

        # Get the forward moves
        for action in actions:
            if (self.state.player_to_move == Player.BLUE
                    and int(action[0]) < int(action[2])):
                ordered_actions.append(action)
                updated_actions.remove(action)
            elif (self.state.player_to_move == Player.RED
                  and int(action[0]) > int(action[2])):
                ordered_actions.append(action)
                updated_actions.remove(action)
        actions = copy.deepcopy(updated_actions)

        # Get the sidewards moves
        for action in actions:
            if int(action[1]) != int(action[3]):
                ordered_actions.append(action)
                updated_actions.remove(action)
        actions = copy.deepcopy(updated_actions)

        # Get the rest of the actions
        for action in actions:
            ordered_actions.append(action)
            updated_actions.remove(action)
        actions = copy.deepcopy(updated_actions)

        return ordered_actions

    @staticmethod
    def alpha_beta_search(state: Board, depth: int = 2):
        """
        This method is for implementing the alpha-beta search algorithm.
        """
        player = state.player_to_move
        move, value = None, None
        if player == Player.BLUE:
            value, move = ActionsFilter._max_value(state=state,
                                               alpha=float("-inf"),
                                               beta=float("inf"),
                                               depth=depth - 1)
        elif player == Player.RED:
            value, move = ActionsFilter._min_value(state=state,
                                               alpha=float("-inf"),
                                               beta=float("inf"),
                                               depth=depth - 1)

        # Total possible nodes without pruning
        # branching_factor = len(state.actions())  # Average branching factor
        branching_factor = min(len(state.actions()), 29) # Estimated average
        depth = 4  # Depth of the search
        total_possible_nodes = (branching_factor ** depth - 1) / (branching_factor - 1)

        # Nodes pruned
        nodes_pruned = total_possible_nodes - ActionsFilter.nodes_visited
        print(f"Possible Nodes: {int(total_possible_nodes)}")
        print(f"Nodes Visited: {ActionsFilter.nodes_visited}")
        ActionsFilter.nodes_visited = 0  # Reset counter
        print(f"Nodes Pruned: {int(nodes_pruned)}")

        
        return value, move

    @staticmethod
    def _max_value(state: Board, alpha: float, beta: float, depth: int):
        ActionsFilter.nodes_visited += 1  # Increment counter
        if state.is_terminal():
            return state.reward(), None
        if not state.is_terminal() and depth == 0:
            return state.material(), None
        value = float("-inf")
        actions_filter = ActionsFilter(state=state, directions=None,
                                       square_whitelist=None)
        move = None
        for action in actions_filter.move_ordering():
            value2, _ = ActionsFilter._min_value(state=state.transition(
                action=action),
                alpha=alpha, beta=beta,
                depth=depth - 1)
            if value2 > value:
                value, move = value2, action
                alpha = max(alpha, value)
            if value >= beta:
                return value, move  # Pruning occurs here
        return value, move

    @staticmethod
    def _min_value(state: Board, alpha: float, beta: float, depth: int):
        ActionsFilter.nodes_visited += 1  # Increment counter
        if state.is_terminal():
            return -state.reward(), None
        if not state.is_terminal() and depth == 0:
            return -state.material(), None
        value = float("inf")
        actions_filter = ActionsFilter(state=state, directions=None,
                                       square_whitelist=None)
        move = None
        for action in actions_filter.move_ordering():
            value2, _ = ActionsFilter._max_value(state=state.transition(
                action=action),
                alpha=alpha, beta=beta,
                depth=depth - 1)
            if value2 < value:
                value, move = value2, action
                beta = min(beta, value)
            if value <= alpha:
                return value, move  # Pruning occurs here
        return value, move


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
        next_profile = [0.0 for action in state.actions()]
        if sum(regret_table) < 0:
            next_profile = [1/len(state.actions())
                            for action in state.actions()]
        else:
            positive_regret_sum = 0
            for regret in regret_table:
                if regret > 0:
                    positive_regret_sum += regret
            for r, regret in enumerate(regret_table):
                if regret > 0:
                    next_profile[r] = regret/positive_regret_sum

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

    def solve(self, abstraction: Abstraction, iterations: int = 100000):
        """
        This runs the counterfactual regret minimization algorithm to produce
        the tables needed by the AI.
        """
        for i in range(iterations):
            for player in [Player.BLUE, Player.RED]:
                arguments = CFRParameters(abstraction=abstraction, current_player=player,
                                          iteration=i, blue_probability=1, red_probability=1)
                self.cfr(params=arguments)


class DepthLimitedCFRTrainer(CFRTrainer):
    """
    This implements a modified CFR that recurses only to a specified depth and
    uses heuristic reward evaluations.
    """

    def __init__(self):
        super().__init__()
        self.vanilla_cfr = CFRTrainer()  # FOr accessing original implementation

    def _cfr_children(self, parameters: CFRParameters, profile: list[float], utilities: list[float],
                      node_utility: float
                      ):
        state, infostate = parameters.abstraction.state, parameters.abstraction.infostate
        if parameters.actions_filter is not None:
            filtered_actions = parameters.actions_filter.filter()
        else:
            filtered_actions = None
        for a, action in enumerate(state.actions()):
            if filtered_actions is not None and action not in filtered_actions:
                utilities[a] = state.material()
                node_utility += profile[a]*utilities[a]
                continue
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
                depth=parameters.depth-1)
            utilities[a] = self.cfr(params=arguments)

            node_utility += profile[a]*utilities[a]

        return node_utility

    def cfr(self, params: CFRParameters):
        """
        This is the recursive algorithm for calculating counterfactual regret.
        """
        abstraction, current_player, blue_probability, red_probability, depth = (
            params.abstraction, params.current_player, params.blue_probability,
            params.red_probability, params.depth
        )

        if abstraction.state.is_terminal():
            return self._terminal_state_utility(abstraction.state, current_player)

        if depth == 0:
            return self._depth_limited_utility(abstraction.state, current_player)

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

    def _depth_limited_utility(self, state: Board, current_player: int):
        if state.player_to_move == current_player:
            return state.material()
        return -state.material()

    def solve(self, abstraction: Abstraction, iterations: int = 10,
              depth: int = 2, actions_filter: ActionsFilter = None):
        """
        This runs the counterfactual regret minimization algorithm to produce
        the tables needed by the AI.
        """
        for i in range(iterations):
            for player in [Player.BLUE, Player.RED]:
                arguments = CFRParameters(abstraction=abstraction, current_player=player,
                                          iteration=i, blue_probability=1, red_probability=1,
                                          depth=depth, actions_filter=actions_filter)
                self.cfr(params=arguments)


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

    def get_cfr_input(self, abstraction: Abstraction, actions_filter: ActionsFilter = None):
        """
        This is for obtaining the CFR controller's chosen action
        """
        valid_actions = abstraction.state.actions()
        action = ""
        trainer = DepthLimitedCFRTrainer()
        trainer.solve(abstraction=abstraction, actions_filter=actions_filter)
        strategy = CFRTrainingSimulator._distill_strategy(
            raw_strategy=trainer.strategy_tables[str(abstraction.infostate)])
        bottom_k = 3  # Number of lowest probabilities to set to 0
        for i in range(bottom_k):
            # Set the lowest probability as the minimum threshold
            threshold = min(strategy)
            for i, probability in enumerate(strategy):
                if probability <= threshold:
                    strategy[i] = 0
        normalizing_sum = sum(strategy)
        if normalizing_sum > 0:
            strategy = [p/normalizing_sum for p in strategy]
        else:
            # Reset options if all evaluated actions seem bad
            strategy = [1/len(valid_actions) for a in valid_actions]

        if actions_filter is None:
            action = random.choices(valid_actions, weights=strategy, k=1)[0]
        else:
            filtered_actions = actions_filter.filter()
            filtered_strategy = []
            for a, action in enumerate(valid_actions):
                if action in filtered_actions:
                    filtered_strategy.append(strategy[a])
            normalizing_sum = sum(filtered_strategy)
            if normalizing_sum > 0:
                filtered_strategy = [
                    p/normalizing_sum for p in filtered_strategy]
            else:
                # Reset options if all evaluated actions seem bad
                filtered_actions, filtered_strategy = valid_actions, strategy
            action = random.choices(
                filtered_actions, weights=filtered_strategy, k=1)[0]

        return action, trainer

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
                "", "", "", "", None)  # Initialize needed values

            turn_number = 1
            while not arbiter_board.is_terminal():
                MatchSimulator._print_game_status(turn_number, arbiter_board, infostates=[
                    blue_infostate, red_infostate],
                    pov=self.pov)
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

                action, trainer = self.get_cfr_input(abstraction=current_abstraction,
                                                     actions_filter=actions_filter)
                print(f"Chosen Move: {action}")
                previous_action = action  # Store for the next iteration
                if self.save_data:
                    self.game_history.append(action)
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

            MatchSimulator._print_result(arbiter_board)


class AlphaBetaTrainingSimulator(MatchSimulator):
    """
    Class for simulating a training time GG match using the alpha-beta search
    algorithm.
    """

    def start(self, iterations: int = 1, target: int = None):
        """
        This method simulates a GG match generating training data, using the
        counterfactual regret minimization algorithm.
        """
        _ = iterations  # Not used in this subclass
        self.blue_formation = list(
            Player.get_sensible_random_formation(
                piece_list=Ranking.SORTED_FORMATION)
        )
        self.red_formation = self._place_in_red_range(list(
            Player.get_sensible_random_formation(
                piece_list=Ranking.SORTED_FORMATION))
        )
        arbiter_board = arbiter_board = Board(self.setup_arbiter_matrix(),
                                              player_to_move=Player.BLUE,
                                              blue_anticipating=False, red_anticipating=False)
        blue_infostate, red_infostate = MatchSimulator._starting_infostates(
            arbiter_board)
        action = ""

        turn_number = 1
        while not arbiter_board.is_terminal():
            MatchSimulator._print_game_status(turn_number, arbiter_board, infostates=[
                blue_infostate, red_infostate],
                pov=self.pov)
            time.sleep(2)
            action = ""  # Initialize variable for storing chosen action

            value, action = ActionsFilter.alpha_beta_search(
                state=arbiter_board, depth=4)
            print(f"Value: {value}")
            arbiter_board = arbiter_board.transition(action)
            print(f"Chosen Move: {action}")

            turn_number += 1

        MatchSimulator._print_result(arbiter_board)
