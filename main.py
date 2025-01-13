import logging

from core import Player, Board

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Sample random formations
    blue_formation = list(Player.get_random_formation(Board.SORTED_FORMATION))
    red_formation = list(Player.get_random_formation(Board.SORTED_FORMATION))

if __name__ == "__main__":
    main()