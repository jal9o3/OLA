from libc.stdlib cimport malloc, free
from cpython cimport array
cimport cython

@cython.boundscheck(False)  # turn off bounds-checking for speed
@cython.wraparound(False)   # turn off negative indexing
def find_unique_locations(list unique_values, list matrix):
    """
    Returns a list of (row, col) tuples where each value in unique_values appears in the matrix.
    """
    cdef int i, j, rows, cols
    cdef int val
    cdef set targets = set(unique_values)
    cdef dict locations = {}
    cdef list row

    rows = len(matrix)

    for i in range(rows):
        row = matrix[i]
        cols = len(row)
        for j in range(cols):
            val = row[j]
            if val in targets:
                locations[val] = (i, j)
                if len(locations) == len(unique_values):
                    return [locations[v] for v in unique_values]

    return None
