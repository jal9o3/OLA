import logging

from core import Player, Board, Ranking, MatchSimulator

def simulate_game(blue_formation: list[int], red_formation: list[int]):
    pass

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Sample random formations
    blue_formation = list(Player.get_random_formation(Ranking.SORTED_FORMATION))
    red_formation = list(Player.get_random_formation(Ranking.SORTED_FORMATION))

    simulator = MatchSimulator(blue_formation, red_formation, 1, False)
    print(simulator.start())

if __name__ == "__main__":
    main()