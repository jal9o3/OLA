"""
This is the entry point for interacting with the OLA engine.
"""
import logging

from OLA.constants import Ranking, Controller
from OLA.core import Player, POV
from OLA.simulation import MatchSimulator
from OLA.training import CFRTrainingSimulator, AlphaBetaTrainingSimulator


def main():
    """
    Here we simulate a GG match.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Sample random formations
    # blue_formation = list(
    #     Player.get_sensible_random_formation(
    #         piece_list=Ranking.SORTED_FORMATION)
    # )
    # red_formation = list(
    #     Player.get_sensible_random_formation(
    #         piece_list=Ranking.SORTED_FORMATION)
    # )

    # match_simulator = MatchSimulator(formations=[blue_formation, red_formation],
    #                                  controllers=[
    #                                      Controller.RANDOM, Controller.RANDOM],
    #                                  save_data=False,
    #                                  pov=POV.RED)
    # match_simulator.start()


    # TRAINING START

    # simulator = CFRTrainingSimulator(formations=[None, None],
    #                                  controllers=None, save_data=False,
    #                                  pov=POV.WORLD)

    simulator = AlphaBetaTrainingSimulator(formations=[None, None],
                                           controllers=None, save_data=False,
                                           pov=POV.WORLD)

    simulator.start(target=1)

    # TRAINING END

if __name__ == "__main__":
    main()
