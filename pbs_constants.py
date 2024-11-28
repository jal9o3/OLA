PBS_ROWS = 42 # 21 pieces per player
PBS_COLS = 5 # see designations below

# Define public belief state columns
PBS_PLAYER = 0 # to which player a piece belongs
PBS_ROW = 1
PBS_COLUMN = 2 # Current location of the piece (if captured, location of capturer)
PBS_KILL_COUNT = 3 # The number of opposing pieces captured by the piece
PBS_CAPTURED = 4 # Whether the piece has been captured

# Annotation indices
# CURRENT_PLAYER = 0, like in world state annotation