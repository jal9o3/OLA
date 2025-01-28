"""
This contains definitions relevant to the training of an AI for GG.
"""

from core import Board, Infostate, Player


class CFRTrainer:
    """
    This is responsible for generating regret and strategy tables using the
    counterfactual regret minimization algorithm.
    """

    def __init__(self):
        self.regret_tables = {}
        self.strategy_tables = {}
        self.profiles = {}

    def cfr(self, state: Board, infostate: Infostate, current_player: int,
            iteration: int, blue_probability: float, red_probability: float):
        """
        This is the recursive algorithm for calculating counterfactual regret.
        """

        opponent = Player.RED if current_player == Player.BLUE else Player.BLUE

        if state.is_terminal() and state.player_to_move == current_player:
            return state.reward()
        if state.is_terminal() and state.player_to_move != current_player:
            return -state.reward()

        node_utility = 0
        utilities = [0.0 for action in state.actions()]

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

        for a, action in enumerate(state.actions()):
            next_state = state.transition(action=action)
            result = state.classify_action_result(action=action,
                                                  new_board=next_state)
            next_infostate = infostate.transition(action=action, result=result)
            # TODO: Check if this needs to have a negative sign
            if state.player_to_move == Player.BLUE:
                utilities[a] = -self.cfr(state=next_state,
                                         infostate=next_infostate,
                                         current_player=current_player,
                                         iteration=iteration,
                                         blue_probability=(
                                             profile[a]*blue_probability),
                                         red_probability=red_probability)
            elif state.player_to_move == Player.RED:
                utilities[a] = -self.cfr(state=next_state,
                                         infostate=next_infostate,
                                         current_player=current_player,
                                         iteration=iteration,
                                         blue_probability=blue_probability,
                                         red_probability=(
                                             profile[a]*red_probability))

            node_utility += profile[a]*utilities[a]

        player_probability = (blue_probability if current_player == Player.BLUE
                              else red_probability)
        opponent_probability = (blue_probability if opponent == Player.BLUE
                                else red_probability)

        if state.player_to_move == current_player:
            for a, action in enumerate(state.actions()):
                regret_table[a] += opponent_probability*(
                    utilities[a] - node_utility)
                strategy_table[a] += player_probability*profile[a]

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
            self.profiles[str(infostate)] = next_profile

        return node_utility

    def solve(self, start_state: Board, start_infostate: Infostate,
              iterations: int = 100000):
        """
        This runs the counterfactual regret minimization algorithm to produce
        the tables needed by the AI.
        """
        for i in range(iterations):
            for player in [Player.BLUE, Player.RED]:
                self.cfr(state=start_state, infostate=start_infostate,
                         current_player=player, iteration=i, blue_probability=1,
                         red_probability=1)
