import random

from generals import *
from infostate_logic import *

class CFR:
    def __init__(self, num_actions):
        self.num_actions = num_actions
        self.regret_sum = [0.0] * num_actions
        self.strategy_sum = [0.0] * num_actions

    def get_strategy(self):
        strategy = [max(0.0, regret) for regret in self.regret_sum]
        normalizing_sum = sum(strategy)
        if normalizing_sum > 0:
            strategy = [s / normalizing_sum for s in strategy]
        else:
            strategy = [1.0 / self.num_actions] * self.num_actions
        self.strategy_sum = [
            self.strategy_sum[i] + strategy[i] for i in range(self.num_actions)]
        return strategy

    def get_average_strategy(self):
        normalizing_sum = sum(self.strategy_sum)
        if normalizing_sum > 0:
            return [s / normalizing_sum for s in self.strategy_sum]
        else:
            return [1.0 / self.num_actions] * self.num_actions

    def update_regret(self, action_utility):
        strategy = self.get_strategy()
        for a in range(self.num_actions):
            self.regret_sum[a] += action_utility[a] - sum(
                strategy[i] * action_utility[i] for i in range(
                    self.num_actions))

    def train(board: list[list[int]], annotation: list[int], 
              valid_actions: list[str]):    
        cfr = CFR(len(valid_actions))
        for _ in range(1000):  # Run for 1000 iterations
            # Simulated utility for each action
            action_utility = [0.0 for _ in range(len(valid_actions))]
            magnitude = 1 if annotation[CURRENT_PLAYER] == BLUE else -1 
            for i, utility in enumerate(action_utility):
                if is_terminal(board, annotation):
                    action_utility[i] = magnitude*reward(board, annotation)
                elif not is_terminal(board, annotation):
                    action_utility[i] = magnitude*reward_estimate(
                        board, annotation)
            cfr.update_regret(action_utility)

        average_strategy = cfr.get_average_strategy()
        return average_strategy
