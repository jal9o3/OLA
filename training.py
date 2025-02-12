"""
This contains definitions relevant to the training of an AI for GG.
"""

import random

from core import Board, Infostate, Player
from simulation import MatchSimulator
from constants import POV, Ranking


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

    def _cfr_children(self, abstraction: Abstraction, profile: list[float],
                      blue_probability: float, red_probability: float, utilities: list[float],
                      node_utility: float, current_player: int, iteration: int
                      ):
        state, infostate = abstraction.state, abstraction.infostate
        for a, action in enumerate(state.actions()):
            next_state, next_infostate = CFRTrainer._get_next(
                state=state, infostate=infostate, action=action)

            new_blue_probability, new_red_probability = (
                CFRTrainer._update_probabilities(
                    state=state, profile=profile, blue_probability=blue_probability,
                    red_probability=red_probability, action_index=a))

            utilities[a] = -self.cfr(abstraction=Abstraction(
                state=next_state, infostate=next_infostate),
                current_player=current_player, iteration=iteration,
                blue_probability=new_blue_probability, red_probability=new_red_probability)

            node_utility += profile[a]*utilities[a]

        return node_utility

    def cfr(self, abstraction: Abstraction, current_player: int,
            iteration: int, blue_probability: float, red_probability: float):
        """
        This is the recursive algorithm for calculating counterfactual regret.
        """
        state, infostate = abstraction.state, abstraction.infostate
        if state.is_terminal() and state.player_to_move == current_player:
            return state.reward()
        if state.is_terminal() and state.player_to_move != current_player:
            return -state.reward()

        node_utility, utilities = CFRTrainer._initialize_utilities(state=state)

        regret_table, strategy_table, profile = self._get_tables(
            state=state, infostate=infostate)

        player_probability, opponent_probability = CFRTrainer._probabilities(
            current_player=current_player, blue_probability=blue_probability,
            red_probability=red_probability)

        node_utility = self._cfr_children(abstraction=abstraction, profile=profile,
                                          blue_probability=blue_probability,
                                          red_probability=red_probability, utilities=utilities,
                                          node_utility=node_utility, current_player=current_player,
                                          iteration=iteration)

        if state.player_to_move == current_player:
            for a, action in enumerate(state.actions()):
                _ = action  # Silences the linter
                regret_table[a] += opponent_probability * \
                    (utilities[a] - node_utility)
                strategy_table[a] += player_probability*profile[a]

            next_profile = CFRTrainer._regret_match(
                state=state, regret_table=regret_table)
            self.profiles[str(infostate)] = next_profile

        return node_utility

    def solve(self, abstraction: Abstraction, iterations: int = 100000):
        """
        This runs the counterfactual regret minimization algorithm to produce
        the tables needed by the AI.
        """
        for i in range(iterations):
            for player in [Player.BLUE, Player.RED]:
                self.cfr(abstraction=abstraction, current_player=player,
                         iteration=i, blue_probability=1, red_probability=1)


class DepthLimitedCFRTrainer(CFRTrainer):
    """
    This implements a modified CFR that recurses only to a specified depth and
    uses heuristic reward evaluations.
    """

    def __init__(self):
        super().__init__()
        self.vanilla_cfr = CFRTrainer()  # FOr accessing original implementation

    def _cfr_children(self, abstraction: Abstraction, profile: list[float],
                      blue_probability: float, red_probability: float, utilities: list[float],
                      node_utility: int, current_player: int, iteration: int, depth: int = None
                      ):
        state, infostate = abstraction.state, abstraction.infostate
        for a, action in enumerate(state.actions()):
            next_state, next_infostate = CFRTrainer._get_next(
                state=state, infostate=infostate, action=action)

            new_blue_probability, new_red_probability = (
                CFRTrainer._update_probabilities(
                    state=state, profile=profile, blue_probability=blue_probability,
                    red_probability=red_probability, action_index=a))

            utilities[a] = -self.cfr(abstraction=Abstraction(
                state=next_state, infostate=next_infostate),
                current_player=current_player, iteration=iteration,
                blue_probability=new_blue_probability, red_probability=new_red_probability,
                depth=depth-1)

            node_utility += profile[a]*utilities[a]

        return node_utility

    def cfr(self, abstraction: Abstraction, current_player: int,
            iteration: int, blue_probability: float, red_probability: float,
            depth: int = 2):
        """
        This is the recursive algorithm for calculating counterfactual regret.
        """
        state, infostate = abstraction.state, abstraction.infostate
        if state.is_terminal() and state.player_to_move == current_player:
            return state.reward()
        if state.is_terminal() and state.player_to_move != current_player:
            return -state.reward()
        if not state.is_terminal() and depth == 0 and state.player_to_move == current_player:
            return state.material()
        if not state.is_terminal() and depth == 0 and state.player_to_move != current_player:
            return -state.material()

        node_utility, utilities = CFRTrainer._initialize_utilities(state=state)

        regret_table, strategy_table, profile = self._get_tables(
            state=state, infostate=infostate)

        player_probability, opponent_probability = CFRTrainer._probabilities(
            current_player=current_player, blue_probability=blue_probability,
            red_probability=red_probability)

        node_utility = self._cfr_children(abstraction=abstraction, profile=profile,
                                          blue_probability=blue_probability,
                                          red_probability=red_probability, utilities=utilities,
                                          node_utility=node_utility, current_player=current_player,
                                          iteration=iteration, depth=depth)

        if state.player_to_move == current_player:
            for a, action in enumerate(state.actions()):
                _ = action  # Silences the linter
                regret_table[a] += opponent_probability * \
                    (utilities[a] - node_utility)
                strategy_table[a] += player_probability*profile[a]

            self.regret_tables[str(infostate)] = regret_table
            self.strategy_tables[str(infostate)] = strategy_table

            next_profile = CFRTrainer._regret_match(
                state=state, regret_table=regret_table)
            self.profiles[str(infostate)] = next_profile

        return node_utility

    def solve(self, abstraction: Abstraction, iterations: int = 10,
              depth=2):
        """
        This runs the counterfactual regret minimization algorithm to produce
        the tables needed by the AI.
        """
        end_game = 12  # Branching when three pieces are left
        for i in range(iterations):
            for player in [Player.BLUE, Player.RED]:
                if len(abstraction.state.actions()) > end_game:
                    self.cfr(abstraction=abstraction, current_player=player,
                             iteration=i, blue_probability=1, red_probability=1,
                             depth=depth)
                else:
                    self.vanilla_cfr.cfr(abstraction=abstraction, current_player=player,
                                         iteration=i, blue_probability=1, red_probability=1)


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

    def get_cfr_input(self, abstraction: Abstraction):
        """
        This is for obtaining the CFR controller's chosen action
        """
        valid_actions = abstraction.state.actions()
        action = ""
        trainer = DepthLimitedCFRTrainer()
        trainer.solve(abstraction=abstraction)
        strategy = CFRTrainingSimulator._distill_strategy(
            raw_strategy=trainer.strategy_tables[str(abstraction.infostate)])
        action = random.choices(valid_actions, weights=strategy, k=1)[0]

        return action

    def start(self):
        """
        This method simulates a GG match generating training data, using the
        counterfactual regret minimization algorithm.
        """
        arbiter_board = Board(self.setup_arbiter_matrix(),
                              player_to_move=Player.BLUE,
                              blue_anticipating=False, red_anticipating=False)
        if self.save_data:
            self.game_history.append(arbiter_board.matrix)

        blue_infostate, red_infostate = MatchSimulator._starting_infostates(
            arbiter_board)

        turn_number = 1
        while not arbiter_board.is_terminal():

            MatchSimulator._print_game_status(turn_number, arbiter_board,
                                              infostates=[
                                                  blue_infostate,
                                                  red_infostate],
                                              pov=self.pov)

            action = ""  # Initialize variable for storing chosen action
            current_infostate = (
                blue_infostate if arbiter_board.player_to_move == Player.BLUE
                else red_infostate)
            current_abstraction = Abstraction(
                state=arbiter_board, infostate=current_infostate)
            action = self.get_cfr_input(abstraction=current_abstraction)
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

        MatchSimulator._print_result(arbiter_board)


if __name__ == "__main__":
    # Sample random formations
    blue_formation = list(
        Player.get_sensible_random_formation(
            piece_list=Ranking.SORTED_FORMATION)
    )
    red_formation = list(
        Player.get_sensible_random_formation(
            piece_list=Ranking.SORTED_FORMATION)
    )

    simulator = CFRTrainingSimulator(formations=[blue_formation, red_formation],
                                     controllers=None, save_data=False,
                                     pov=POV.WORLD)
    simulator.start()
