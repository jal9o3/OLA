import logging

from core import Player, Board, Ranking, MatchSimulator


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Sample random formations
    blue_formation = list(
        Player.get_random_formation(piece_list=Ranking.SORTED_FORMATION)
    )
    red_formation = list(
        Player.get_random_formation(piece_list=Ranking.SORTED_FORMATION)
    )

    match_simulator = MatchSimulator(blue_formation, red_formation, mode=1,
                                     save_data=False)
    print(match_simulator.start())


if __name__ == "__main__":
    main()
