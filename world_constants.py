# Global constants for Game of the Generals
ROWS = 8
COLUMNS = 9

INITIAL_ARMY = 21 # Number of pieces a player obtains at the start

# Power Rankings of Pieces
BLANK = 0 # Unoccupied Square
FLAG = 1 # Philippine Flag
PRIVATE = 2 # One Chevron
SERGEANT = 3 # Three Chevrons
SECOND_LIEUTENANT = 4 # One Magdalo Triangle
FIRST_LIEUTENANT = 5 # Two Magdalo Triangles
CAPTAIN = 6 # Three Magdalo Triangles
MAJOR = 7 # One Magdalo Seven-Ray Sun
LIEUTENANT_COLONEL = 8 # Two Magdalo Seven-Ray Suns
COLONEL = 9 # Three Magdalo Seven-Ray Suns
BRIGADIER_GENERAL = 10 # One Star
MAJOR_GENERAL = 11 # Two Stars
LIEUTENANT_GENERAL = 12 # Three Stars
GENERAL = 13 # Four Stars
GENERAL_OF_THE_ARMY = 14 # Five Stars
SPY = 15 # Two Prying Eyes
# Red pieces will be denoted 16 (FLAG) to 30 (SPY)
BLUE_UNKNOWN = 31 # Placeholder for unidentified blue enemy pieces
RED_UNKNOWN = 32

PIECE_SELECTION = [
    1, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15
] # The initial pieces

# Designations of players
BLUE = 1 # Moves first
RED = 2

# Designations of the annotation indices
CURRENT_PLAYER = 0
WAITING_BLUE_FLAG = 1 # If blue flag reaches enemy base with an adjacent enemy
WAITING_RED_FLAG = 2 # Same for the red flag

# Gameplay modes
RANDOM_VS_RANDOM = 0
HUMAN_VS_RANDOM = 1

# State display levels
WORLD = 0 # Every piece value is visible
# BLUE = 1; RED = 2 (as above)
BLIND = 3 # None of the piece values are visible

# Challenge results
DRAW = 0
WIN = 1
OCCUPY = 2
LOSS = 3
