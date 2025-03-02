"""
This is the entry point for interacting with the OLA engine.
"""
import logging

from OLA.constants import Ranking, Controller
from OLA.core import Player, POV
from OLA.simulation import MatchSimulator


def main():
    """
    Here we simulate a GG match.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Sample random formations
    blue_formation = list(
        Player.get_sensible_random_formation(
            piece_list=Ranking.SORTED_FORMATION)
    )
    red_formation = list(
        Player.get_sensible_random_formation(
            piece_list=Ranking.SORTED_FORMATION)
    )

    match_simulator = MatchSimulator(formations=[blue_formation, red_formation],
                                     controllers=[
                                         Controller.HUMAN, Controller.RANDOM],
                                     save_data=False,
                                     pov=POV.RED)
    match_simulator.start()


if __name__ == "__main__":
    main()
