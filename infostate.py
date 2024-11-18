import logging

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

def private_observation(infostate, action, result):

    # Successful attacker

    # Failed attacker

    # Draw

    pass
