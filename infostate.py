import logging, copy

logging.basicConfig(level=logging.WARNING)

# GLobal constants
from world_constants import *

INFOROWS = 42 # 21 pieces per player
INFOCOLS = 19 # see designations below

# Define information state columns
PLAYER = 0 # to which player a piece belongs
# 1 - 15 is the probability of being pieces 1 - 15
ROW = 16
COLUMN = 17 # Current location of the piece (if captured, location of capturer)
CAPTURED = 18 # Whether the piece has been captured

# Annotation indices
# CURRENT_PLAYER = 0, like in the world state annotation
WAITING_FLAG = 1 # Corresponds to WAITING_BLUE or WAITING_RED flags in world
POV_PLAYER = 2 # to which the infostate belongs

def bayes_theorem(hypothesis, evidence):
    # p(H|E) =
    # p(E|H)*p(H)/p(E)
    pass

def conditional_probability(hypothesis, evidence):
    # p(H|E) =
    # p(H intersection E) / p(E)
    pass


def private_observation(infostate, infostate_annotation, action, result):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    def handle_draw_update(piece):
        if infostate_annotation[POV_PLAYER] == BLUE:
            piece[ROW] = ROWS + 1
            piece[COLUMN] = COLUMNS + 1 # Send piece outside the board
        else:
            piece[ROW] = ROWS + 2
            piece[COLUMN] = COLUMNS + 2
        piece[CAPTURED] = 1

    for i, piece in enumerate(infostate):
        logger.debug(f"{i}")
        if (piece[ROW] == int(action[0]) 
            and piece[COLUMN] == int(action[1])):
            # Draw
            if result == DRAW:
                logger.debug("attacker draw")
                handle_draw_update(piece)
            # Successful attacker or occupant or loss
            # Denotes either relocation or location of successful defender
            elif result == WIN or result == OCCUPY or result == LOSS:
                logger.debug(f"attacker {result}")
                piece[ROW] = int(action[2])
                piece[COLUMN] = int(action[3])
                if result == LOSS and piece[PLAYER] == infostate_annotation[CURRENT_PLAYER]:
                    piece[CAPTURED] = 1

    for i, piece in enumerate(infostate):
        logger.debug(f"{i}")
        if (piece[ROW] == int(action[2])
            and piece[COLUMN] == int(action[3])):
            logger.debug("found defender")
            if result == DRAW:
                logger.debug("defender draw")
                handle_draw_update(piece)
            elif result == WIN and piece[PLAYER] != infostate_annotation[CURRENT_PLAYER]:
                logger.debug("defender win")
                piece[CAPTURED] = 1
            # No defender in occupation
            # No location update for winning defender

    infostate_annotation[CURRENT_PLAYER] = RED if infostate_annotation[CURRENT_PLAYER] == BLUE else BLUE 

    return infostate, infostate_annotation
            

