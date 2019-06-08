import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Union
from NumericalTools import linear_interpolation_nearest_neighbour

class Wing(object):

    def __init__(self, halfspan: Union[int, float]):

        # Initialize all parameters defining the wing
        self.b = halfspan
        self.MAC = None
        self.x_LEMAC = None
        self.cr = None
        self.ct = None
        self.taper = None
        self.chord_distribution = None
        self.sweep_distribution = None
        self.twist_distribution = None
        self.airfoil_distribution = None
        self.dihedral_distribution = None

    @staticmethod
    def __calculate_MAC(c: np.array):
        return np.average(c)

    @staticmethod
    def __number_input_allocation(number: int or float, span: int or float, key: str,target: dict or None, n_steps: int = 100):

        if target is None:
            target = {}

        target['y'] = np.linspace(0, span, n_steps)
        target[key] = np.array([number for _ in target['y']])

    @staticmethod
    def __array_input_allocation(array: list or np.array, span: int or float, key: str, target: dict or None, n_steps: int = 100):

        if target is None:
            target = {}

        if type(array) == list:
            array = np.array(array)

        target['y'] = np.linspace(0, span, n_steps)

        if array.shape[0] > array.shape[1]:
            target = {
                key: array[:, 0],
                "y": array[:, 1]
            }

        elif array.shape[0] < array.shape[1]:
            target = {
                key: array[0, :],
                "y": array[1, :]
            }


    def set_sweep(self, sweep: Union[int, float, callable, list, np.array, dict], n_steps: int = 100):

        sweeptype = type(sweep)

        if sweeptype in [int, float]:
            self.sweep_distribution = {
                "sweep": np.array([sweep for _ in np.linspace(0, self.b, n_steps)]),
                "y": np.linspace(0, self.b, n_steps)
            }

        elif sweeptype in [list, np.array]:
            sweep = np.array(sweep) if sweeptype is list else sweep

            if sweep.shape[0] > sweep.shape[1]:
                self.sweep_distribution = {
                    "sweep": sweep[:, 0],
                    "y": sweep[:, 1]
                }

            elif sweep.shape[0] < sweep.shape[1]:
                self.sweep_distribution = {
                    "sweep": sweep[0, :],
                    "y": sweep[1, :]
                }

        elif sweeptype is callable:

            self.sweep_distribution = {
                "sweep":
            }

    def set_chord(self, c: Union[int, float, callable, list, np.array, dict], n_steps: int = 100):

        ctype = type(c)

        if ctype in [int, float]:
            self.cr = c
            self.ct = c
            self.chord_distribution = {
                "c": np.array([c for _ in np.linspace(0, self.b, n_steps)]),
                "y": np.linspace(0, self.b, n_steps)
            }
            self.taper = 1

        elif ctype in [list, np.array]:
            c = np.array(c) if ctype is list else c
            self.cr = c[0]
            self.ct = c[-1]

            if c.shape[0] >= c.shape[1]:
                self.chord_distribution = {
                    "c": c[:, 0],
                    "y": c[:, 1]
                }
            elif c.shape[0] < c.shape[1]:
                self.chord_distribution = {
                    "c": c[0, :],
                    "y": c[1, :]
                }

            self.taper = self.ct/self.cr

        elif ctype == callable:
            self.cr = c(0)
            self.ct = c(self.b)
            self.chord_distribution = {
                "c": np.array([c(yi) for yi in np.linspace(0, self.b, n_steps)]),
                "y": np.linspace(0, self.b, n_steps)
            }

            self.taper = self.ct/self.cr

        elif ctype == dict:
            self.cr = c["c"][0]
            self.ct = c["c"][-1]
            self.chord_distribution = {
                "c": np.array(c["c"]),
                "y": np.array(c["y"])
            }

            self.taper = self.ct/self.cr

        else:
            raise TypeError("Invalid Input")

        self.MAC = self.__calculate_MAC(self.chord_distribution['c'])
