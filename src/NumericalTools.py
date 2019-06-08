import numpy as np


def derive(f, h=10e-5):
    return lambda x: (f(x+h) - f(x))/h


def linear_interpolation_nearest_neighbour(X, Y):

    def linear_function(x0):

        diff = float('inf')
        for idx, xi in enumerate(X):
            prev_diff = float(diff)
            diff = abs(x0 - xi)

            if prev_diff < diff:

                dx = X[idx] - X[idx-1]
                dy = Y[idx] - Y[idx-1]

                return dy/dx*(x0 - X[idx-1]) + Y[idx-1]

        raise ValueError("Value outside defined range")
