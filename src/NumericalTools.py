import numpy as np


def derive(f, h=10e-5):
    return lambda x: (f(x+h) - f(x))/h
