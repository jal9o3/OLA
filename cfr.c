#include <stdbool.h> // To use bool type and true/false values
#include <stdio.h> 
#include <stdlib.h> 
#include <string.h>

// Global constants for Game of the Generals
#define ROWS 8
#define COLUMNS 9

#define INITIAL_ARMY 21 // Number of pieces a player obtains at the start

// Power Rankings of Pieces
#define BLANK 0 // Unoccupied Square
#define FLAG 1 // Philippine Flag
#define PRIVATE 2 // One Chevron
#define SERGEANT 3 // Three Chevrons
#define SECOND_LIEUTENANT 4 // One Magdalo Triangle
#define FIRST_LIEUTENANT 5 // Two Magdalo Triangles
#define CAPTAIN 6 // Three Magdalo Triangles
#define MAJOR 7 // One Magdalo Seven-Ray Sun
#define LIEUTENANT_COLONEL 8 // Two Magdalo Seven-Ray Suns
#define COLONEL 9 // Three Magdalo Seven-Ray Suns
#define BRIGADIER_GENERAL 10 // One Star
#define MAJOR_GENERAL 11 // Two Stars
#define LIEUTENANT_GENERAL 12 // Three Stars
#define GENERAL 13 // Four Stars
#define GENERAL_OF_THE_ARMY 14 // Five Stars
#define SPY 15 // Two Prying Eyes
// Red pieces will be denoted 16 (FLAG) to 30 (SPY)
#define BLUE_UNKNOWN 31 // Placeholder for unidentified blue enemy pieces
#define RED_UNKNOWN 32

// The initial pieces
int PIECES[] = {1, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15};

// The initial pieces + six spaces
int FORMATION_COMPONENTS[] = {
    0, 0, 0, 0, 0, 0,
    1, 2, 2, 2, 2, 2, 2,
    3, 4, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 15
};

// Designations of players
#define BLUE 1 // Moves first
#define RED 2

// Designations of the annotation indices
#define CURRENT_PLAYER 0
#define WAITING_BLUE_FLAG 1 // If blue flag reaches enemy base with an adjacent enemy
#define WAITING_RED_FLAG 2 // Same for the red flag

// Gameplay modes
#define RANDOM_VS_RANDOM 0
#define HUMAN_VS_RANDOM 1
#define CFR_VS_CFR 2

// State display levels
#define WORLD 0 // Every piece value is visible
// #define BLUE 1 // RED = 2 (as above)
#define BLIND 3 // None of the piece values are visible

// Challenge results
#define DRAW 0
#define WIN 1
#define OCCUPY 2
#define LOSS 3

// Function for checking adjacent enemy pieces in waiting flags
bool has_none_adjacent(int flag_col, int nrow[]) {
    // If not at the left or rightmost edge of the board
    if (flag_col != 0 && flag_col != COLUMNS - 1) {
        // Check both squares to the left and right
        if (!nrow[flag_col - 1] && !nrow[flag_col + 1]) {
            return true;
        }
    } else if (flag_col == 0 && !nrow[flag_col + 1]) {
        // If flag is at the first column and the square next to it is empty
        return true;
    } else if (flag_col == COLUMNS - 1 && !nrow[flag_col - 1]) {
        // If flag is at the last column and the square before it is empty
        return true;
    }
    return false;
}

// Function to determine if the current state is a terminal state
bool is_terminal(int board[ROWS][COLUMNS], int annotation[]) {

    // If either of the flags have been captured
    bool flag_captured = false;
    bool spy_flag_captured = false;

    for (int i = 0; i < ROWS; i++) {
        for (int j = 0; j < COLUMNS; j++) {
            if (board[i][j] == FLAG) {
                flag_captured = true;
            }
            if (board[i][j] == SPY + FLAG) {
                spy_flag_captured = true;
            }
        }
    }

    if (!flag_captured || !spy_flag_captured) {
        return true;
    }

    // If the blue flag is on the other side of the board
    for (int j = 0; j < COLUMNS; j++) {
        if (board[ROWS - 1][j] == FLAG) {
            if (annotation[WAITING_BLUE_FLAG]) {
                return true;
            } else {
                int flag_col = j; // Get the flag's column number
                return has_none_adjacent(flag_col, board[ROWS - 1]);
            }
        }
    }

    // Do the same checking for the red flag
    for (int j = 0; j < COLUMNS; j++) {
        if (board[0][j] == SPY + FLAG) {
            if (annotation[WAITING_RED_FLAG]) {
                return true;
            } else {
                int flag_col = j; // Get the flag's column number
                return has_none_adjacent(flag_col, board[0]);
            }
        }
    }

    // If none of the checks have been passed, it is not a terminal state
    return false;
}

// Function to measure overall reward of terminal states
// 1 is a blue win, -1 is a red win
int reward(int board[ROWS][COLUMNS], int annotation[]) {
    // A non-terminal state is not eligible for assessment
    if (!is_terminal(board, annotation)) {
        // Log message (no equivalent logging function here, so we just return a special value)
        return 0; // Returning 0 to indicate that state is not terminal (equivalent to Python's None)
    }

    // Blue flag captured
    bool flag_exists = false;
    bool spy_flag_exists = false;

    for (int i = 0; i < ROWS; i++) {
        for (int j = 0; j < COLUMNS; j++) {
            if (board[i][j] == FLAG) {
                flag_exists = true;
            }
            if (board[i][j] == SPY + FLAG) {
                spy_flag_exists = true;
            }
        }
    }

    if (!flag_exists) {
        return -1;
    }

    // Red flag captured
    if (!spy_flag_exists) {
        return 1;
    }

    // Blue flag reaches red side
    for (int j = 0; j < COLUMNS; j++) {
        if (board[ROWS - 1][j] == FLAG) {
            // Log message (no equivalent logging function here, so we just comment it)
            // logger.debug("blue flag in red side");
            if (annotation[WAITING_BLUE_FLAG]) {
                return 1;
            } else {
                int flag_col = j; // Get the flag's column number
                if (has_none_adjacent(flag_col, board[ROWS - 1])) {
                    return 1;
                }
            }
        }
    }

    // Red flag reaches blue side
    for (int j = 0; j < COLUMNS; j++) {
        if (board[0][j] == SPY + FLAG) {
            if (annotation[WAITING_RED_FLAG]) {
                return -1;
            } else {
                int flag_col = j; // Get the flag's column number
                if (has_none_adjacent(flag_col, board[0])) {
                    return -1;
                }
            }
        }
    }

    // If none of the conditions are met, return 0 (indicating it's not terminal)
    return 0;
}

// Function to check if a square is valid
bool is_valid(int square, int range_start, int range_end) {
    return !(range_start <= square && square <= range_end) || square == BLANK;
}

// Function to obtain all possible actions for each state
char** actions(int board[ROWS][COLUMNS], int annotation[], int *move_count) {
    int current_player = annotation[CURRENT_PLAYER];
    // Set ranges of piece designations
    int range_start, range_end;
    if (current_player == BLUE) {
        range_start = FLAG;
        range_end = SPY;
    } else {
        range_start = SPY + FLAG;
        range_end = SPY + SPY;
    }

    // Initialize a dynamic array to store moves
    char **moves = (char **)malloc(100 * sizeof(char *));
    // printf("Moves ptr: %p\n", (void *)moves);
    for (int i = 0; i < 100; i++) {
        moves[i] = (char *)malloc(5 * sizeof(char)); // Each move will have 4 characters + null terminator
    }
    *move_count = 0; // Initialize move count

    // Iterate over every square of the board
    for (int row = 0; row < ROWS; row++) {
        for (int column = 0; column < COLUMNS; column++) {
            int square = board[row][column];
            // Check for a piece that belongs to the current player
            if (square >= range_start && square <= range_end) {
                // Check for allied pieces in adjacent squares:
                if (row != ROWS - 1) { // UP
                    if (is_valid(board[row + 1][column], range_start, range_end)) {
                        sprintf(moves[*move_count], "%d%d%d%d", row, column, row + 1, column);
                        (*move_count)++;
                    }
                }
                if (row != 0) { // DOWN
                    if (is_valid(board[row - 1][column], range_start, range_end)) {
                        sprintf(moves[*move_count], "%d%d%d%d", row, column, row - 1, column);
                        (*move_count)++;
                    }
                }
                if (column != COLUMNS - 1) { // RIGHT
                    if (is_valid(board[row][column + 1], range_start, range_end)) {
                        sprintf(moves[*move_count], "%d%d%d%d", row, column, row, column + 1);
                        (*move_count)++;
                    }
                }
                if (column != 0) { // LEFT
                    if (is_valid(board[row][column - 1], range_start, range_end)) {
                        sprintf(moves[*move_count], "%d%d%d%d", row, column, row, column - 1);
                        (*move_count)++;
                    }
                }
            }
        }
    }

    // Free everything that exceeds the move count
    for (int i = *move_count; i < 100; i++) {
        free(moves[i]);
    }

    // Reallocate the array to the actual move count 
    moves = (char **)realloc(moves, *move_count * sizeof(char *));

    return moves;
}

// Function to move a piece from one position to another
void move_piece(int start_row, int start_col, int end_row, int end_col, int board[ROWS][COLUMNS], int new_board[ROWS][COLUMNS]) {
    new_board[end_row][end_col] = board[start_row][start_col];
    new_board[start_row][start_col] = BLANK;
}

// Function to handle challenges between pieces
void handle_challenges(int challenger_value, int target_value, int start_row, int start_col, int end_row, int end_col, int board[ROWS][COLUMNS], int new_board[ROWS][COLUMNS]) {
    // Edge case where PRIVATE defeats SPY
    if (challenger_value == PRIVATE && target_value == SPY) {
        move_piece(start_row, start_col, end_row, end_col, board, new_board);
        return;
    } else if (challenger_value == SPY && target_value == PRIVATE) {
        new_board[start_row][start_col] = BLANK; // remove losing attacker
        return;
    }
    // Stronger piece or flag challenge
    if (challenger_value > target_value || (challenger_value == FLAG && target_value == FLAG)) {
        move_piece(start_row, start_col, end_row, end_col, board, new_board);
    } else if (challenger_value < target_value) {
        new_board[start_row][start_col] = BLANK; // remove losing attacker
    } else {
        // Remove both in tie
        new_board[start_row][start_col] = BLANK;
        new_board[end_row][end_col] = BLANK;
    }
}

// Define a struct to hold the new board and annotation
typedef struct {
    int new_board[ROWS][COLUMNS];
    int new_annotation[3]; // Assuming annotation has 3 elements
} TransitionResult;

TransitionResult transition(int board[ROWS][COLUMNS], int annotation[], char action[]) {
    TransitionResult result;

    // Copy the board and annotation to the struct
    memcpy(result.new_board, board, sizeof(int) * ROWS * COLUMNS);
    memcpy(result.new_annotation, annotation, sizeof(int) * 3); // Assuming annotation has 3 elements

    int blue_flag_col, red_flag_col;

    // Obtain indices of starting and destination squares
    int start_row = action[0] - '0';
    int start_col = action[1] - '0';
    int end_row = action[2] - '0';
    int end_col = action[3] - '0';

    int current_player = annotation[CURRENT_PLAYER];
    int range_start = (current_player == BLUE) ? FLAG : FLAG + SPY;
    int range_end = (current_player == BLUE) ? SPY : SPY + SPY;

    // Check if starting square's piece belongs to current player
    if (!(board[start_row][start_col] != BLANK &&
          range_start <= board[start_row][start_col] && board[start_row][start_col] <= range_end)) {
        return result;
    }

    // Check if destination square's piece does not belong to the current player
    if (board[end_row][end_col] != BLANK &&
        range_start <= board[end_row][end_col] && board[end_row][end_col] <= range_end) {
        return result;
    }

    // If the destination square is blank, move selected piece to it
    if (board[end_row][end_col] == BLANK) {
        move_piece(start_row, start_col, end_row, end_col, board, result.new_board);
    } else if (current_player == BLUE) { // Handle challenges
        int opponent_value = board[end_row][end_col] - SPY;
        handle_challenges(board[start_row][start_col], opponent_value, start_row, start_col, end_row, end_col, board, result.new_board);
    } else if (current_player == RED) {
        int own_value = board[start_row][start_col] - SPY;
        handle_challenges(own_value, board[end_row][end_col], start_row, start_col, end_row, end_col, board, result.new_board);
    }

    result.new_annotation[CURRENT_PLAYER] = (current_player == BLUE) ? RED : BLUE;

    // Find the indices of the flags
    for (int i = 0; i < ROWS; i++) {
        for (int j = 0; j < COLUMNS; j++) {
            if (board[i][j] == FLAG) {
                blue_flag_col = j;
            }
            else if (board[i][j] == SPY + FLAG) {
                red_flag_col = j;
            }
        }
    }

    // If the blue flag reaches the other side
    if (memchr(board[ROWS - 1], FLAG, COLUMNS * sizeof(int)) != NULL && 
        !annotation[WAITING_BLUE_FLAG] &&
        !has_none_adjacent(board[ROWS - 1][blue_flag_col], board[ROWS - 1])) {
        result.new_annotation[WAITING_BLUE_FLAG] = 1;
    } 
    // Check for the red flag
    else if (memchr(board[0], SPY + FLAG, COLUMNS * sizeof(int)) != NULL &&
             !annotation[WAITING_RED_FLAG] &&
             !has_none_adjacent(board[0][red_flag_col], board[0])) {
        result.new_annotation[WAITING_RED_FLAG] = 1;
    }

    return result;
}

typedef struct {
    double node_util;
    double *strategy;
} CFRResult;

CFRResult cfr(int board[ROWS][COLUMNS], int annotation[], double blue_probability, double red_probability, int current_depth, int max_depth) {
    CFRResult result;
    int player = annotation[CURRENT_PLAYER];
    int opponent = (player == BLUE) ? RED : BLUE;

    // Return payoff for 'terminal' states
    if ((current_depth == max_depth && is_terminal(board, annotation)) || is_terminal(board, annotation)) {
        result.node_util = (player == BLUE) ? reward(board, annotation) : -reward(board, annotation);
        result.strategy = NULL;
        return result;
    } else if (current_depth == max_depth && !is_terminal(board, annotation)) {
        result.node_util = 0;
        result.strategy = NULL;
        return result;
    }

    // Initialize strategy
    int move_count;
    char **valid_actions = actions(board, annotation, &move_count);
    int actions_n = move_count;
    result.strategy = (double *)malloc(actions_n * sizeof(double));
    double *regret_sum = (double *)calloc(actions_n, sizeof(double));
    
    for (int i = 0; i < actions_n; i++) {
        result.strategy[i] = 1.0 / actions_n; // Uniform strategy
    }

    // Initialize action utilities
    double *util = (double *)calloc(actions_n, sizeof(double));
    double node_util = 0;

    // Iterate over children nodes and recursively call cfr
    for (int a = 0; a < actions_n; a++) {
        TransitionResult next = transition(board, annotation, valid_actions[a]);
        if (player == BLUE) {
            CFRResult sub_result = cfr(next.new_board, next.new_annotation, red_probability * result.strategy[a], blue_probability, current_depth + 1, max_depth);
            util[a] = -sub_result.node_util;
            // Deallocate intermediate strategy result
            free(sub_result.strategy);
        } else {
            CFRResult sub_result = cfr(next.new_board, next.new_annotation, blue_probability, red_probability * result.strategy[a], current_depth + 1, max_depth);
            util[a] = -sub_result.node_util;
            // Deallocate intermediate strategy result
            free(sub_result.strategy);
        }
        // Calculate node utility
        node_util += result.strategy[a] * util[a];
    }

    // Calculate regret sum
    for (int a = 0; a < actions_n; a++) {
        double regret = util[a] - node_util;
        regret_sum[a] += (player == BLUE ? red_probability : blue_probability) * regret;
    }

    // Normalize regret sum to find strategy for this node
    double normalizing_sum = 0;
    for (int a = 0; a < actions_n; a++) {
        if (regret_sum[a] > 0) {
            normalizing_sum += regret_sum[a];
        }
    }

    for (int a = 0; a < actions_n; a++) {
        if (normalizing_sum > 0) {
            result.strategy[a] = regret_sum[a] / normalizing_sum;
        } else {
            result.strategy[a] = 1.0 / actions_n;
        }
        // Update node utility with regret-matched strategy
        node_util += result.strategy[a] * util[a];
    }

    result.node_util = node_util;

    // Free allocated memory for valid actions
    for (int i = 0; i < actions_n; i++) {
        free(valid_actions[i]);
    }
    // printf("valid_actions ptr: %p\n", (void *)valid_actions);
    free(valid_actions);
    free(util);
    free(regret_sum);

    return result;
}

int main() {
    int board[8][9] = {
        {0, 7, 0, 0, 0, 2, 4, 0, 5},
        {11, 10, 2, 2, 1, 8, 12, 9, 14},
        {2, 0, 2, 3, 15, 2, 13, 15, 6},
        {0, 0, 0, 0, 0, 0, 0, 0, 0},
        {0, 0, 0, 0, 0, 0, 0, 0, 0},
        {28, 0, 20, 0, 16, 21, 24, 17, 26},
        {30, 22, 0, 0, 23, 30, 25, 29, 17},
        {17, 17, 18, 0, 17, 17, 27, 0, 19}
    };

    int annotation[3] = {BLUE, 0, 0};

    CFRResult result;

    for (int i = 0; i < 5; i++) {
        result = cfr(board, annotation, 1, 1, 0, 4);
        free(result.strategy);
        printf("%d\n", i);
    }

    // Printing the matrix
    // for (int i = 0; i < 8; i++) {
    //     for (int j = 0; j < 9; j++) {
    //         printf("%3d ", board[i][j]);
    //     }
    //     printf("\n");
    // }

    return 0;
}