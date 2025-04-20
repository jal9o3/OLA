"""
This contains function definitions that are independent of other core GG 
objects.
"""

import random

from OLA.constants import Ranking


def get_random_permutation(elements: list):
    """
    This function receives a list and returns a shuffled copy of it.
    """
    list_to_shuffle = elements[:]
    random.shuffle(list_to_shuffle)
    shuffled_list = list_to_shuffle
    return tuple(shuffled_list)


def get_blank_matrix(rows: int, columns: int):
    """
    This function returns a matrix of the specified number of rows and columns,
    with all entries set to 0 (aka BLANK).
    """
    return [[Ranking.BLANK for col in range(columns)] for row in range(rows)]


def get_hex_uppercase_string(number: int):
    """
    This is for saving print space for pieces with ranks above 9.
    """
    hex_string = hex(number)[2:].upper()

    return hex_string


def find_indices(lst: list, value):
    """
    Find all the indices in which the value appears in a given list.
    """
    return [index for index, element in enumerate(lst) if element == value]


def is_column_zero_from_row(matrix: list[list[int]], start_row: int, col: int):
    """
    Checks if all entries below a row in a given column are all zero.
    """
    for row in range(start_row, len(matrix)):
        if matrix[row][col] != 0:
            return False
    return True


def is_column_zero_up_to_row(matrix: list[list[int]], start_row: int, col: int):
    """
    Checks if all entries above a row in a given column are all zero.
    """
    for row in range(start_row, -1, -1):
        if matrix[row][col] != 0:
            return False
    return True


def find_unique_value(matrix: list[list[int]], target: int):
    """
    Finds the first occurrence of a specified value in a 2D list (matrix).

    Args:
        matrix (list of list of int/float): The matrix to search within.
        target (int/float): The value to find in the matrix.

    Returns:
        tuple: A tuple (row_index, col_index) indicating the position of the 
        target value.
        None: If the target value is not found in the matrix.
    """
    for row_index, row in enumerate(matrix):
        for col_index, element in enumerate(row):
            if element == target:
                return row_index, col_index
    return None  # Return None if the target value is not found


def defeats(attacker: int, defender: int):
    """
    Determines if the first (attacker) piece rank defeats the second (defender)
    piece rank. A draw is considered a defeat for the attacker. This function
    is intended to be used with the access point heuristic in the evaluation.
    """
    if attacker == defender:
        if attacker == Ranking.FLAG:
            return True  # Unneccessary clause but included for thoroughness
        return False

    if attacker == Ranking.PRIVATE and defender == Ranking.SPY:
        return True

    if attacker == Ranking.SPY and defender == Ranking.PRIVATE:
        return False

    if attacker > defender:
        return True

    return False
