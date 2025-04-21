# cython: boundscheck=False, wraparound=False, cdivision=True
# Disabling boundscheck and wraparound boosts speed at the cost of safety

cdef int PRIVATE = 2
cdef int SPY = 15
cdef int RED_OFFSET = SPY
cdef int BOARD_ROWS = 8
cdef int FORWARD_WEIGHT = 2

cpdef int evaluation(list matrix):
    cdef int blue_sum = 0
    cdef int red_sum = 0
    cdef int i, j, piece
    cdef int forward_bonus

    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            piece = matrix[i][j]

            if PRIVATE <= piece <= SPY:
                blue_sum += piece
                forward_bonus = min(i * FORWARD_WEIGHT, 5 * FORWARD_WEIGHT)
                blue_sum += forward_bonus * piece

            elif PRIVATE + RED_OFFSET <= piece <= 2 * RED_OFFSET:
                piece_val = piece - RED_OFFSET
                red_sum += piece_val
                forward_bonus = min((BOARD_ROWS - 1 - i) * FORWARD_WEIGHT, 5 * FORWARD_WEIGHT)
                red_sum += forward_bonus * piece_val

    return blue_sum - red_sum
