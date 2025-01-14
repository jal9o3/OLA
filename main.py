"""
This is the entry point for interacting with the OLA engine.
"""
import logging

from core import Player, Ranking, MatchSimulator


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

    match_simulator = MatchSimulator(blue_formation, red_formation, mode=1,
                                     save_data=False)
    match_simulator.start()


if __name__ == "__main__":
    main()
