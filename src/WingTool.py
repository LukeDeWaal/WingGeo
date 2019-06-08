import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Union
from NumericalTools import linear_interpolation_nearest_neighbour
from AirFoilTool import FiveDigitNACA, FourDigitNACA

class Wing(object):

    def __init__(self, halfspan: Union[int, float], n_steps: int = 100):

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

        # Final Coordinates of the wing
        self.__n_steps = n_steps
        self.datapoints = np.zeros((3, self.__n_steps))


    """
    Detail-Level Methods go below here
    """
    @staticmethod
    def __calculate_MAC(c: np.array):
        return np.average(c)

    """
    The Following 4 Methods are for the correct assignment of the data describing the wing.
    All data is eventually stored in dictionaries but can be inputted as:
        - Integers and floats for constant values along span
        - Lists or Arrays for custom definitions of the variable
        - Callables as a different way of customizing the variable
        - Dictionaries which contain the y coordinates and their variables in a list or array 
          can also be inputted with the correct key
    """
    @staticmethod
    def __number_input_allocation(number: int or float or str, span: int or float, key: str,target: dict or None, n_steps: int, airfoil: bool = False):

        if target is None:
            target = {}

        if airfoil is False:
            target['y'] = np.linspace(0, span, n_steps)
            target[key] = np.array([number for _ in target['y']])

        elif airfoil is True:
            number = str(number)

            if len(number) == 4:
                coordinates = FourDigitNACA(number).calculate_coordinates(cosine_spacing=True)

            elif len(number) == 5:
                coordinates = FiveDigitNACA(number).calculate_coordinates(cosine_spacing=True)

            else:
                raise ValueError("Unexpected Input")

            # TODO: This is an incorrect implementation, correct the way coordinates are saved
            target['x'] = np.concatenate((coordinates['XU'], coordinates['XL'][::-1]))
            target['y'] = np.linspace(0, span, n_steps)
            target['z'] = np.concatenate((coordinates['YU'], coordinates['YL'][::-1]))



    @staticmethod
    def __array_input_allocation(array: list or np.array, key: str, target: dict or None, airfoil: bool = False):

        if target is None:
            target = {}

        if airfoil is False:

            if type(array) == list:
                array = np.array(array)

            if array.shape[0] > array.shape[1]:
                target[key] = array[:, 0]
                target["y"] = array[:, 1]

            elif array.shape[0] < array.shape[1]:
                target[key] = array[0, :]
                target["y"] = array[1, :]

        elif airfoil is True:

            if type(array[0][0]) == str:
                for number in array[0]:
                    number = str(number)

                    if len(number) == 4:
                        coordinates = FourDigitNACA(number).calculate_coordinates(cosine_spacing=True)

                    elif len(number) == 5:
                        coordinates = FiveDigitNACA(number).calculate_coordinates(cosine_spacing=True)

                    else:
                        raise ValueError("Unexpected Input")

            elif type(array[1][0]) == str:
                pass
            #TODO: Lots to finish here


            if array.shape[0] > array.shape[1]:
                target["x"] = array[:, 0]
                target["y"] = array[:, 1]
                target["z"] = array[:, 2]

            elif array.shape[0] < array.shape[1]:
                target["x"] = array[0, :]
                target["y"] = array[1, :]
                target["z"] = array[2, :]

    @staticmethod
    def __callable_input_allocation(function: callable, span: int or float, key: str, target: dict or None, n_steps: int):
        
        if target is None:
            target = {}

        target['y'] = np.linspace(0, span, n_steps)
        target[key] = np.array([function(yi) for yi in target['y']])
        
    @staticmethod
    def __dictionary_input_allocation(dictionary: dict, key: str, target: dict or None):
        
        if target is None:
            target = {}

        target['y'] = dictionary['y']
        target[key] = dictionary[key]

    """
    These methods will be used by the user to create their wing
    """
    def set_airfoil(self, airfoil: Union[int, str, callable, list, np.array, dict]):
        
        airfoiltype = type(airfoil)

        # TODO: Make airfoil selection process more modular
        if airfoiltype in [int, str]:
            airfoil = str(airfoil) if airfoiltype is int else airfoil
            self.__number_input_allocation(airfoil, self.b, 'airfoil', self.airfoil_distribution, self.__n_steps, airfoil=True)

        elif airfoiltype in [list, np.array]:
            self.__array_input_allocation(airfoil, 'airfoil', self.airfoil_distribution, airfoil=True)

        elif airfoiltype is callable(airfoil):
            self.__callable_input_allocation(airfoil, self.b, 'airfoil', self.airfoil_distribution, self.__n_steps)

        elif airfoiltype is dict:
            self.__dictionary_input_allocation(airfoil, 'airfoil', self.airfoil_distribution)

        else:
            raise TypeError("Invalid Input")
    
    def set_twist(self, twist: Union[int, float, callable, list, np.array, dict]):
        
        twisttype = type(twist)

        if twisttype in [int, float]:
            self.__number_input_allocation(twist, self.b, 'twist', self.twist_distribution, self.__n_steps)

        elif twisttype in [list, np.array]:
            self.__array_input_allocation(twist, 'twist', self.twist_distribution)

        elif twisttype is callable:
            self.__callable_input_allocation(twist, self.b, 'twist', self.twist_distribution, self.__n_steps)

        elif twisttype is dict:
            self.__dictionary_input_allocation(twist, 'twist', self.twist_distribution)

        else:
            raise TypeError("Invalid Input")
    
    def set_dihedral(self, dihedral: Union[int, float, callable, list, np.array, dict]):
        
        dihedraltype = type(dihedral)
        
        if dihedraltype in [int, float]:
            self.__number_input_allocation(dihedral, self.b, 'dihedral', self.dihedral_distribution, self.__n_steps)

        elif dihedraltype in [list, np.array]:
            self.__array_input_allocation(dihedral, 'dihedral', self.dihedral_distribution)

        elif dihedraltype is callable:
            self.__callable_input_allocation(dihedral, self.b, 'dihedral', self.dihedral_distribution, self.__n_steps)

        elif dihedraltype is dict:
            self.__dictionary_input_allocation(dihedral, 'dihedral', self.dihedral_distribution, )

        else:
            raise TypeError("Invalid Input")
        
    def set_sweep(self, sweep: Union[int, float, callable, list, np.array, dict]):

        sweeptype = type(sweep)
    
        if sweeptype in [int, float]:
            self.__number_input_allocation(sweep, self.b, 'sweep', self.sweep_distribution, self.__n_steps)

        elif sweeptype in [list, np.array]:
            self.__array_input_allocation(sweep, 'sweep', self.sweep_distribution, )

        elif sweeptype is callable:
            self.__callable_input_allocation(sweep, self.b, 'sweep', self.sweep_distribution, self.__n_steps)
            
        elif sweeptype is dict:
            self.__dictionary_input_allocation(sweep, 'sweep', self.sweep_distribution)
            
        else:
            raise TypeError("Invalid Input")

    def set_chord(self, c: Union[int, float, callable, list, np.array, dict]):

        ctype = type(c)

        if ctype in [int, float]:
            self.cr = c
            self.ct = c
            self.taper = 1
            self.__number_input_allocation(c, self.b, 'chord', self.chord_distribution, self.__n_steps)

        elif ctype in [list, np.array]:

            self.__array_input_allocation(c, 'chord', self.chord_distribution)
            self.cr = self.chord_distribution['chord'][0]
            self.ct = self.chord_distribution['chord'][-1]
            self.taper = self.ct/self.cr

        elif ctype == callable:
            self.cr = c(0)
            self.ct = c(self.b)
            self.taper = self.ct/self.cr
            self.__callable_input_allocation(c, self.b, 'chord', self.chord_distribution, self.__n_steps)

        elif ctype == dict:
            self.__dictionary_input_allocation(c, 'chord', self.chord_distribution)
            self.cr = self.chord_distribution['chord'][0]
            self.ct = self.chord_distribution['chord'][0]
            self.taper = self.ct/self.cr

        else:
            raise TypeError("Invalid Input")

        self.MAC = self.__calculate_MAC(self.chord_distribution['chord'])


    """
    Once all desired variables are defined, the wing will have to be 'assembled'. 
    Aka. The 3D coordinates will have to be calculated.
    """
    def construct(self, double_sided: bool = False):
        pass
