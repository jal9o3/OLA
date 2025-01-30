"""
This contains definitions relevant to the training of an AI for GG.
"""

from core import Board, Infostate, Player


class Abstraction:
    """
    This replaces the theoretical full history of the game.
    """

    def __init__(self, state: Board, infostate: Infostate):
        self.state = state
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
            profile = [0.0 for action in state.actions()]
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
                      current_player: int, iteration: int
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
                                          current_player=current_player, iteration=iteration)

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
                      current_player: int, iteration: int, depth: int = None
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
            depth: int = 8):
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
        if not state.is_terminal() and depth == 0 and state.player_to_move == current_player:
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
                                          current_player=current_player, iteration=iteration,
                                          depth=depth)

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

    def solve(self, abstraction: Abstraction, iterations: int = 100000,
              depth=8):
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
