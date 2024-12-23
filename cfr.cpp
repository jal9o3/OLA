#include <vector>
#include <algorithm> // For std::find
#include <iostream> // For logging
#include <string>
#include <cstring> // For std::memcpy
#include <cmath> // For logarithmic operations if needed

// Global constants for Game of the Generals
const int ROWS = 8;
const int COLUMNS = 9;

const int INITIAL_ARMY = 21; // Number of pieces a player obtains at the start

// Power Rankings of Pieces
const int BLANK = 0; // Unoccupied Square
const int FLAG = 1; // Philippine Flag
const int PRIVATE = 2; // One Chevron
const int SERGEANT = 3; // Three Chevrons
const int SECOND_LIEUTENANT = 4; // One Magdalo Triangle
const int FIRST_LIEUTENANT = 5; // Two Magdalo Triangles
const int CAPTAIN = 6; // Three Magdalo Triangles
const int MAJOR = 7; // One Magdalo Seven-Ray Sun
const int LIEUTENANT_COLONEL = 8; // Two Magdalo Seven-Ray Suns
const int COLONEL = 9; // Three Magdalo Seven-Ray Suns
const int BRIGADIER_GENERAL = 10; // One Star
const int MAJOR_GENERAL = 11; // Two Stars
const int LIEUTENANT_GENERAL = 12; // Three Stars
const int GENERAL = 13; // Four Stars
const int GENERAL_OF_THE_ARMY = 14; // Five Stars
const int SPY = 15; // Two Prying Eyes
// Red pieces will be denoted 16 (FLAG) to 30 (SPY)
const int BLUE_UNKNOWN = 31; // Placeholder for unidentified blue enemy pieces
const int RED_UNKNOWN = 32;

const std::vector<int> PIECES = {
    1, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15
}; // The initial pieces

const std::vector<int> FORMATION_COMPONENTS = {
    0, 0, 0, 0, 0, 0,
    1, 2, 2, 2, 2, 2, 2,
    3, 4, 5, 6, 7, 8, 9, 10, 
    11, 12, 13, 14, 15, 15
}; // The initial pieces + six spaces

// Designations of players
const int BLUE = 1; // Moves first
const int RED = 2;

// Designations of the annotation indices
const int CURRENT_PLAYER = 0;
const int WAITING_BLUE_FLAG = 1; // If blue flag reaches enemy base with an adjacent enemy
const int WAITING_RED_FLAG = 2; // Same for the red flag

// Gameplay modes
const int RANDOM_VS_RANDOM = 0;
const int HUMAN_VS_RANDOM = 1;
const int CFR_VS_CFR = 2;

// State display levels
const int WORLD = 0; // Every piece value is visible
// const int BLUE = 1; // Already defined above
// const int RED = 2; // Already defined above
const int BLIND = 3; // None of the piece values are visible

// Challenge results
const int DRAW = 0;
const int WIN = 1;
const int OCCUPY = 2;
const int LOSS = 3;

extern "C" {

    bool has_none_adjacent(int flag_col, const std::vector<int>& nrow) {
        // If not at the left or rightmost edge of the board
        if (flag_col != 0 && flag_col != COLUMNS - 1) {
            // Check both squares to the left and right
            if (nrow[flag_col - 1] == 0 && nrow[flag_col + 1] == 0) {
                return true;
            }
        } else if (flag_col == 0 && nrow[flag_col + 1] == 0) {
            // If flag is at the first column and the square next to it is empty
            return true;
        } else if (flag_col == COLUMNS - 1 && nrow[flag_col - 1] == 0) {
            // If flag is at the last column and the square before it is empty
            return true;
        }
        return false;
    }

    bool is_terminal(const std::vector<std::vector<int>>& board, const std::vector<int>& annotation) {
        // Logging (simple version)
        std::cout << "Checking for terminal state..." << std::endl;
        
        // If either of the flags have been captured
        if (std::none_of(board.begin(), board.end(), [](const std::vector<int>& row) {
                return std::find(row.begin(), row.end(), FLAG) != row.end();
            }) || std::none_of(board.begin(), board.end(), [](const std::vector<int>& row) {
                return std::find(row.begin(), row.end(), SPY + FLAG) != row.end();
            })) {
            return true;
        }
        
        // If the blue flag is on the other side of the board
        if (std::find(board.back().begin(), board.back().end(), FLAG) != board.back().end()) {
            if (annotation[WAITING_BLUE_FLAG]) {
                return true;
            } else {
                auto it = std::find(board.back().begin(), board.back().end(), FLAG);
                int flag_col = std::distance(board.back().begin(), it); // Get the flag's column number
                return has_none_adjacent(flag_col, board.back());
            }
        }

        // Do the same checking for the red flag
        if (std::find(board.front().begin(), board.front().end(), SPY + FLAG) != board.front().end()) {
            if (annotation[WAITING_RED_FLAG]) {
                return true;
            } else {
                auto it = std::find(board.front().begin(), board.front().end(), SPY + FLAG);
                int flag_col = std::distance(board.front().begin(), it); // Get the flag's column number
                return has_none_adjacent(flag_col, board.front());
            }
        }

        // If none of the checks have been passed, it is not a terminal state
        return false;
    }

    int reward(const std::vector<std::vector<int>>& board, const std::vector<int>& annotation) {
        // Logging (simple version)
        std::cout << "Checking reward for terminal state..." << std::endl;
        
        // A non-terminal state is not eligible of assessment
        if (!is_terminal(board, annotation)) {
            std::cout << "State is not terminal" << std::endl;
            return 0; // Return 0 for non-terminal state (use an appropriate value)
        }
        
        // Blue flag captured
        if (std::none_of(board.begin(), board.end(), [](const std::vector<int>& row) {
                return std::find(row.begin(), row.end(), FLAG) != row.end();
            })) {
            return -1;
        }
        
        // Red flag captured
        if (std::none_of(board.begin(), board.end(), [](const std::vector<int>& row) {
                return std::find(row.begin(), row.end(), SPY + FLAG) != row.end();
            })) {
            return 1;
        }

        // Blue flag reaches red side
        if (std::find(board.back().begin(), board.back().end(), FLAG) != board.back().end()) {
            std::cout << "Blue flag in red side" << std::endl;
            if (annotation[WAITING_BLUE_FLAG]) {
                return 1;
            } else {
                auto it = std::find(board.back().begin(), board.back().end(), FLAG);
                int flag_col = std::distance(board.back().begin(), it); // Get the flag's column number
                if (has_none_adjacent(flag_col, board.back())) {
                    return 1;
                }
            }
        }

        // Red flag reaches blue side
        if (std::find(board.front().begin(), board.front().end(), SPY + FLAG) != board.front().end()) {
            if (annotation[WAITING_RED_FLAG]) {
                return -1;
            } else {
                auto it = std::find(board.front().begin(), board.front().end(), SPY + FLAG);
                int flag_col = std::distance(board.front().begin(), it); // Get the flag's column number
                if (has_none_adjacent(flag_col, board.front())) {
                    return -1;
                }
            }
        }

        // Return 0 if no terminal condition met (use an appropriate value)
        return 0;
    }

    bool is_valid(int square, int range_start, int range_end) {
        return !(range_start <= square && square <= range_end) || square == BLANK;
    }

    std::vector<std::string> actions(const std::vector<std::vector<int>>& board, const std::vector<int>& annotation) {
        // Logging (simple version)
        std::cout << "Generating possible actions..." << std::endl;

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

        std::vector<std::string> moves;
        // Iterate over every square of the board
        for (int row = 0; row < ROWS; ++row) {
            for (int column = 0; column < COLUMNS; ++column) {
                int square = board[row][column];
                // Check for a piece that belongs to the current player
                if (square >= range_start && square <= range_end) {
                    // Check for allied pieces in adjacent squares:
                    if (row != ROWS - 1) { // UP
                        if (is_valid(board[row + 1][column], range_start, range_end)) {
                            moves.push_back(std::to_string(row) + std::to_string(column) + std::to_string(row + 1) + std::to_string(column));
                        }
                    }
                    if (row != 0) { // DOWN
                        if (is_valid(board[row - 1][column], range_start, range_end)) {
                            moves.push_back(std::to_string(row) + std::to_string(column) + std::to_string(row - 1) + std::to_string(column));
                        }
                    }
                    if (column != COLUMNS - 1) { // RIGHT
                        if (is_valid(board[row][column + 1], range_start, range_end)) {
                            moves.push_back(std::to_string(row) + std::to_string(column) + std::to_string(row) + std::to_string(column + 1));
                        }
                    }
                    if (column != 0) { // LEFT
                        if (is_valid(board[row][column - 1], range_start, range_end)) {
                            moves.push_back(std::to_string(row) + std::to_string(column) + std::to_string(row) + std::to_string(column - 1));
                        }
                    }
                }
            }
        }
        return moves;
    }

    void move_piece(std::vector<std::vector<int>>& new_board, int start_row, int start_col, int end_row, int end_col) {
        new_board[end_row][end_col] = new_board[start_row][start_col];
        new_board[start_row][start_col] = BLANK;
    }

    void handle_challenges(std::vector<std::vector<int>>& new_board, int start_row, int start_col, int end_row, int end_col, int challenger_value, int target_value) {
        // Edge case where PRIVATE defeats SPY
        if (challenger_value == 2 && target_value == 15) { // PRIVATE defeats SPY
            move_piece(new_board, start_row, start_col, end_row, end_col);
            return;
        } else if (challenger_value == 15 && target_value == 2) { // SPY defeated by PRIVATE
            new_board[start_row][start_col] = BLANK; // remove losing attacker
            return;
        }
        // Stronger piece or flag challenge
        if (challenger_value > target_value || (challenger_value == 1 && target_value == 1)) {            
            move_piece(new_board, start_row, start_col, end_row, end_col);
        } else if (challenger_value < target_value) {
            new_board[start_row][start_col] = BLANK; // remove losing attacker
        } else {
            // Remove both in tie
            new_board[start_row][start_col] = BLANK;
            new_board[end_row][end_col] = BLANK;
        }
    }

    std::pair<std::vector<std::vector<int>>, std::vector<int>> transition(const std::vector<std::vector<int>>& board, const std::vector<int>& annotation, const std::string& action) {
        // Logging (simple version)
        std::cout << "Performing transition..." << std::endl;

        std::vector<std::vector<int>> new_board = board;
        std::vector<int> new_annotation = annotation;

        // Obtain indices of starting and destination squares
        int start_row = action[0] - '0';
        int start_col = action[1] - '0';
        int end_row = action[2] - '0';
        int end_col = action[3] - '0';

        int current_player = annotation[CURRENT_PLAYER];
        int range_start = (current_player == BLUE) ? FLAG : FLAG + SPY;
        int range_end = (current_player == BLUE) ? SPY : SPY + SPY;

        // Check if starting square's piece belongs to current player
        if (!(board[start_row][start_col] != BLANK && range_start <= board[start_row][start_col] && board[start_row][start_col] <= range_end)) {
            return std::make_pair(new_board, new_annotation); // return unchanged state
        }
        
        // Check if destination square's piece does not belong to the current player
        if (board[end_row][end_col] != BLANK && range_start <= board[end_row][end_col] && board[end_row][end_col] <= range_end) {
            return std::make_pair(new_board, new_annotation); // return unchanged state
        }

        // If the destination square is blank, move selected piece to it
        if (board[end_row][end_col] == BLANK) {
            move_piece(new_board, start_row, start_col, end_row, end_col);
        } else if (current_player == BLUE) { // Handle challenges
            int opponent_value = board[end_row][end_col] - SPY;
            handle_challenges(new_board, start_row, start_col, end_row, end_col, board[start_row][start_col], opponent_value);
        } else if (current_player == RED) {
            int own_value = board[start_row][start_col] - SPY;
            handle_challenges(new_board, start_row, start_col, end_row, end_col, own_value, board[end_row][end_col]);
        }
            
        new_annotation[CURRENT_PLAYER] = (current_player == BLUE) ? RED : BLUE;
        // If the blue flag reaches the other side
        if (std::find(new_board.back().begin(), new_board.back().end(), FLAG) != new_board.back().end() && !annotation[WAITING_BLUE_FLAG] && !has_none_adjacent(std::distance(new_board.back().begin(), std::find(new_board.back().begin(), new_board.back().end(), FLAG)), new_board.back())) {
            new_annotation[WAITING_BLUE_FLAG] = 1;
        }
        // Check for the red flag
        if (std::find(new_board.front().begin(), new_board.front().end(), SPY + FLAG) != new_board.front().end() && !annotation[WAITING_RED_FLAG] && !has_none_adjacent(std::distance(new_board.front().begin(), std::find(new_board.front().begin(), new_board.front().end(), SPY + FLAG)), new_board.front())) {
            new_annotation[WAITING_RED_FLAG] = 1;
        }
        return std::make_pair(new_board, new_annotation);
    }

    std::pair<double, std::vector<double>> cfr(
        const std::vector<std::vector<int>>& board,
        const std::vector<int>& annotation,
        double blue_probability, double red_probability,
        int current_depth, int max_depth
    ) {
        std::cout << "Running CFR..." << std::endl;

        int player = annotation[CURRENT_PLAYER];
        int opponent = (player == BLUE) ? RED : BLUE;

        // Return payoff for 'terminal' states
        if ((current_depth == max_depth && is_terminal(board, annotation)) || is_terminal(board, annotation)) {
            if (player == BLUE) {
                return {reward(board, annotation), {}};
            } else {
                return {-reward(board, annotation), {}};
            }
        } else if (current_depth == max_depth && !is_terminal(board, annotation)) {
            return {0, {}}; // Replace with neural network perhaps
        }

        // Initialize strategy
        std::vector<std::string> valid_actions = actions(board, annotation);
        int actions_n = valid_actions.size();
        std::vector<double> strategy(actions_n, 1.0 / actions_n); // Uniform strategy
        std::vector<double> regret_sum(actions_n, 0.0);

        // Initialize action utilities
        std::vector<double> util(actions_n, 0.0);
        // Initialize node utility
        double node_util = 0;

        // Iterate over children nodes and recursively call cfr
        for (int a = 0; a < actions_n; ++a) {
            const std::string& action = valid_actions[a];
            auto [next_board, next_annotation] = transition(board, annotation, action);
            if (player == BLUE) {
                auto result = cfr(next_board, next_annotation, red_probability * strategy[a], blue_probability, current_depth + 1, max_depth);
                util[a] = -result.first;
            } else {
                auto result = cfr(next_board, next_annotation, blue_probability, red_probability * strategy[a], current_depth + 1, max_depth);
                util[a] = -result.first;
            }
            // Calculate node utility
            node_util += strategy[a] * util[a];
        }

        if (current_depth == 0) {
            std::cout << "Uniform Utility: " << node_util << std::endl;
        }

        // Calculate regret sum
        for (int a = 0; a < actions_n; ++a) {
            double regret = util[a] - node_util;
            regret_sum[a] += (player == BLUE ? red_probability : blue_probability) * regret;
        }

        // Normalize regret sum to find strategy for this node
        std::vector<double> new_strategy(actions_n, 0.0);
        double normalizing_sum = 0;
        for (int a = 0; a < actions_n; ++a) {
            if (regret_sum[a] > 0) {
                normalizing_sum += regret_sum[a];
            }
        }

        for (int a = 0; a < actions_n; ++a) {
            if (normalizing_sum > 0) {
                new_strategy[a] = regret_sum[a] / normalizing_sum;
            } else {
                new_strategy[a] = 1.0 / actions_n;
            }
            // Update node utility with regret-matched strategy
            node_util += new_strategy[a] * util[a];
        }

        // Return node utility
        return {node_util, new_strategy};
    }
}