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
