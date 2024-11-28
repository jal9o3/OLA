INFOROWS = 42 # 21 pieces per player
INFOCOLS = 21 # see designations below

# Define information state columns
PLAYER = 0 # to which player a piece belongs
# 1 - 15 is the probability of being pieces 1 - 15
ROW = 16
COLUMN = 17 # Current location of the piece (if captured, location of capturer)
RANGE_BOT = 18 # Lowest possible value of a piece
RANGE_TOP = 19 # Highest possible value of a piece, these are equal once identified
CAPTURED = 20 # Whether the piece has been captured

# Annotation indices
# CURRENT_PLAYER = 0, like in the world state annotation
WAITING_FLAG = 1 # Corresponds to WAITING_BLUE or WAITING_RED flags in world
POV_PLAYER = 2 # to which the infostate belongs

# The number of unique permutations of the initial pieces
# VALUE_PERMUTATIONS_N = (math.factorial(21))/math.factorial(6)*math.factorial(2)

# SAMPLE_N = ((1.96**2)*0.5*(1 - 0.5))/0.05**2
# Representative sample size
# ADJUSTED_SAMPLE_N = SAMPLE_N/(1 + ((SAMPLE_N - 1)/VALUE_PERMUTATIONS_N))