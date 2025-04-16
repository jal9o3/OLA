"""
This is the entry point for interacting with the OLA engine.
"""

from OLA.constants import Ranking, Controller
from OLA.core import Player, POV
from OLA.simulation import MatchSimulator
from OLA.training import CFRTrainingSimulator


def main():
    """
    Here we simulate a GG match.
    """
    choice = input("1 - Simulate match\n2 - Generate training data\n>> ")

    if choice == "1":
        print("Selected match simulation.")
        # Sample random formations
        blue_formation = list(Player.get_sensible_random_formation(
            piece_list=Ranking.SORTED_FORMATION))
        red_formation = list(Player.get_sensible_random_formation(
            piece_list=Ranking.SORTED_FORMATION))

        match_simulator = MatchSimulator(formations=[blue_formation, red_formation],
                                         controllers=[
                                             Controller.RANDOM, Controller.RANDOM],
                                         save_data=False,
                                         pov=POV.RED)
        match_simulator.start()
    elif choice == "2":
        print("Selected data generation.")
        simulator = CFRTrainingSimulator(formations=[None, None],
                                         controllers=None, save_data=False,
                                         pov=POV.WORLD)
        simulator.start(target=20)


if __name__ == "__main__":
    main()
