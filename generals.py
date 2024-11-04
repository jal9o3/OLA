# Global constants for Game of the Generals
ROWS = 8
COLUMNS = 9

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
UNKNOWN = 31 # Placeholder for unidentified enemy pieces

# Designations of players
BLUE = 1 # Moves first
RED = 2

# Designations of the annotation indices
CURRENT_PLAYER = 0
WAITING_BLUE_FLAG = 1 # If blue flag reaches enemy base with an adjacent enemy
WAITING_RED_FLAG = 2 # Same for the red flag

def main():
    # Board for arbiter
    board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    annotation = [BLUE, 0, 0]
    
    # Boards for both player POVs
    blue_board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    red_board = [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]
    
    # Initial formations span three rows
    blue_formation = [BLANK for _ in range(COLUMNS) for _ in range(ROWS)]
    red_formation = [BLANK for _ in range(COLUMNS) for _ in range(ROWS)]

    # formation_temp = input("BLUE formation: ")
    formation_temp = "1 15 15 2 2 2 2 0 2 3 4 5 6 7 8 9 10 11 0 13 14 0 0 12 0 2 0"
    # Preprocess input
    for i, p in enumerate(formation_temp.split(" ")):
        blue_formation[i] = int(p)

    # Place pieces on blue board
    i = 0
    for row in range(ROWS-3, ROWS):
        for column in range(COLUMNS):
            if i < len(blue_formation):
                blue_board[row][column] = blue_formation[i]
                i += 1

    # Flip the blue board matrix:
    # Flip the blue board matrix upside down 
    blue_board = blue_board[::-1]
    # Flip each blue board row left to right 
    blue_board = [row[::-1] for row in blue_board]

    #print_matrix(blue_board)

    # formation_temp = input("RED formation: ")
    formation_temp = "1 15 0 2 2 2 2 2 2 3 4 5 6 7 0 9 10 11 12 13 14 0 0 8 0 15 0"
    # Preprocess input
    for i, p in enumerate(formation_temp.split(" ")):
        if int(p) != BLANK:
            red_formation[i] = int(p) + SPY # Red pieces range from 15 to 30

    # Place pieces on red board
    i = 0
    for row in range(ROWS-3, ROWS):
        for column in range(COLUMNS):
            if i < len(red_formation):
                red_board[row][column] = red_formation[i]
                i += 1

    #print_matrix(red_board)

    # Perform matrix addition 
    board = [[blue_board[i][j] + red_board[i][j] for j in range(COLUMNS)] for i in range(len(board))]


    # Flip the board matrix for the standard POV (blue on the bottom side):
    standard_pov = board[::-1]
    standard_pov = [row[::-1] for row in standard_pov] # flip rows
    
    print_matrix(board)

    print_matrix(standard_pov)

def is_terminal(board, annotation):
    # If either of the flags have been captured
    if FLAG not in board or SPY + FLAG not in board:
        return True

    # Procedure for checking adjacent enemy pieces in waiting flags
    def has_adjacent(flag_col):
        # If not at the left or rightmost edge of the board
        if flag_col != 0 and flag_col != COLUMNS - 1:
            # Check both squares to the left and right
            if not board[-1][flag_col - 1] and not board[-1][flag_col + 1]:
                return True
        elif flag_col == 0 and not board[-1][flag_col + 1]:
            # If flag is at the first column
            # and the square next to it is empty
            return True
        elif flag_col == COLUMNS - 1 and not board[-1][flag_col - 1]:
            # If flag is at the last column
            # and the square before it is empty
            return True
    
    # If the blue flag is on the other side of the board
    if FLAG in board[-1]:
        # If flag has already survived a turn
        if annotation[WAITING_BLUE_FLAG]:
            return True
        else:
            flag_col = board[-1].index(FLAG) # Get the flag's column number
            return has_adjacent(flag_col)

    # Do the same checking for the red flag
    if SPY + FLAG in board[0]:
        if annotation[WAITING_RED_FLAG]:
            return True
        else:
            flag_col = board[0].index(FLAG)
            return has_adjacent(flag_col)

    # If none of the checks have been passed, it is not a terminal state
    return False
            
def print_matrix(board):
    print()
    for row in board: 
        for elem in row: 
            print(f"{elem:2}", end=' ') 
        print()
    print()       

if __name__ == "__main__":
    main()
