import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Union
from NumericalTools import linear_interpolation_nearest_neighbour
from AirFoilTool import FiveDigitNACA, FourDigitNACA, LoadedAirfoil
from colorama import Fore, Style


class DataStorage(object):

    def __init__(self):

        self.__data_dict = None
        self.__data_array = None
        self.__length = None
        self.__keys = None

    def get_dictionary(self):
        return self.__data_dict

    def get_array(self):
        return self.__data_array

    def __get_y_keys(self):
        self.__keys = list(self.__data_dict.keys())

    def __array_to_dict(self):

        unique_y = set(self.__data_array[1,:])
        series_length = 0

        y0 = self.__data_array[1,0]
        for idx, yi in enumerate(self.__data_array[1,1:]):
            if yi == y0:
                continue
            else:
                series_length = idx+1
                break

        for counter, y in enumerate(unique_y):
            self.__data_dict[y] = {
                'x': self.__data_array[0, counter*series_length:(counter+1):series_length],
                'z': self.__data_array[2, counter*series_length:(counter+1):series_length]
            }

    def __dict_to_array(self):

        ny = len(self.__data_dict)
        nxz = len(self.__data_dict[self.__keys[0]]['x'])

        self.__data_array = np.zeros((3, ny*nxz))

        for idx1, (y, value) in enumerate(self.__data_dict.items()):
            for idx2, (x, z) in enumerate(zip(self.__data_dict[y]['x'], self.__data_dict[y]['z'])):
                self.__data_array[:,idx1*nxz + idx2] = np.array([x, y, z])

    def set_data(self, data: Union[np.array, dict, list]):

        if type(data) == list:
            data = np.array(data)

        if type(data) == dict:

            self.__data_dict = dict(data)
            self.__get_y_keys()
            self.__dict_to_array()

        elif type(data) == np.array:

            self.__data_array = np.array(data)
            self.__array_to_dict()
            self.__get_y_keys()


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

        self.transformation_order = []

        # Final Coordinates of the wing
        self.__n_steps = n_steps
        self.__yrange = np.linspace(0, self.b, self.__n_steps)
        self.data_container = DataStorage()


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
    def __number_input_allocation(code: str, span: int or float, key: str, target: dict or None, n_steps: int, airfoil: bool = False):

        if target is None:
            target = dict()

        if airfoil is False:
            target['y'] = np.linspace(0, span, n_steps)
            target[key] = np.array([code for _ in target['y']])

        elif airfoil is True:
            target[code] = (0, 1, None, None)

        return target

    @staticmethod
    def __array_input_allocation(array: list or np.array, key: str, target: dict or None):

        # TODO: Interpolate the values of array to match discretization

        if target is None:
            target = {}

        if type(array) == list:
            array = np.array(array)

        if array.shape[0] > array.shape[1]:
            target[key] = array[:, 0]
            target["y"] = array[:, 1]

        elif array.shape[0] < array.shape[1]:
            target[key] = array[0, :]
            target["y"] = array[1, :]

        return target

    @staticmethod
    def __callable_input_allocation(function: callable, span: int or float, key: str, target: dict or None, n_steps: int):
        
        if target is None:
            target = {}

        target['y'] = np.linspace(0, span, n_steps)
        target[key] = np.array([function(yi) for yi in target['y']])

        return target
        
    @staticmethod
    def __dictionary_input_allocation(dictionary: dict, key: str, target: dict or None, airfoil=False):
        
        if target is None:
            target = {}

        if airfoil is False:
            target['y'] = dictionary['y']
            target[key] = dictionary[key]

        elif airfoil is True:

            for key, value in dictionary.items():
                target[key] = value

        return target

    """
    These methods will be used by the user to create their wing
    """
    def set_airfoil(self, airfoil: Union[str, dict]):
        
        airfoiltype = type(airfoil)

        if airfoiltype is str:
            self.airfoil_distribution = self.__number_input_allocation(airfoil, self.b, 'airfoil', self.airfoil_distribution, self.__n_steps, airfoil=True)

        elif airfoiltype is dict:
            self.airfoil_distribution = self.__dictionary_input_allocation(airfoil, 'airfoil', self.airfoil_distribution, airfoil=True)

        else:
            raise TypeError("Invalid Input")
    
    def set_twist(self, twist: Union[int, float, callable, list, np.array, dict]):
        
        twisttype = type(twist)

        if twisttype in [int, float]:
            self.twist_distribution = self.__number_input_allocation(twist, self.b, 'twist', self.twist_distribution, self.__n_steps)

        elif twisttype in [list, np.array]:
            self.twist_distribution = self.__array_input_allocation(twist, 'twist', self.twist_distribution)

        elif callable(twist):
            self.twist_distribution = self.__callable_input_allocation(twist, self.b, 'twist', self.twist_distribution, self.__n_steps)

        elif twisttype is dict:
            self.twist_distribution = self.__dictionary_input_allocation(twist, 'twist', self.twist_distribution)

        else:
            raise TypeError("Invalid Input")

        self.transformation_order.append(self.__apply_twist)
    
    def set_dihedral(self, dihedral: Union[int, float, callable, list, np.array, dict]):
        
        dihedraltype = type(dihedral)
        
        if dihedraltype in [int, float]:
            self.dihedral_distribution = self.__number_input_allocation(dihedral, self.b, 'dihedral', self.dihedral_distribution, self.__n_steps)

        elif dihedraltype in [list, np.array]:
            self.dihedral_distribution = self.__array_input_allocation(dihedral, 'dihedral', self.dihedral_distribution)

        elif callable(dihedral):
            self.dihedral_distribution = self.__callable_input_allocation(dihedral, self.b, 'dihedral', self.dihedral_distribution, self.__n_steps)

        elif dihedraltype is dict:
            self.dihedral_distribution = self.__dictionary_input_allocation(dihedral, 'dihedral', self.dihedral_distribution, )

        else:
            raise TypeError("Invalid Input")

        self.transformation_order.append(self.__apply_dihedral)
        
    def set_sweep(self, sweep: Union[int, float, callable, list, np.array, dict]):

        sweeptype = type(sweep)
    
        if sweeptype in [int, float]:
            self.sweep_distribution = self.__number_input_allocation(sweep, self.b, 'sweep', self.sweep_distribution, self.__n_steps)

        elif sweeptype in [list, np.array]:
            self.sweep_distribution = self.__array_input_allocation(sweep, 'sweep', self.sweep_distribution, )

        elif callable(sweep):
            self.sweep_distribution = self.__callable_input_allocation(sweep, self.b, 'sweep', self.sweep_distribution, self.__n_steps)
            
        elif sweeptype is dict:
            self.sweep_distribution = self.__dictionary_input_allocation(sweep, 'sweep', self.sweep_distribution)
            
        else:
            raise TypeError("Invalid Input")

        self.transformation_order.append(self.__apply_sweep)

    def set_chord(self, c: Union[int, float, callable, list, np.array, dict]):

        ctype = type(c)

        if ctype in [int, float]:
            self.cr = c
            self.ct = c
            self.taper = 1
            self.chord_distribution = self.__number_input_allocation(c, self.b, 'chord', self.chord_distribution, self.__n_steps)

        elif ctype in [list, np.array]:

            self.chord_distribution = self.__array_input_allocation(c, 'chord', self.chord_distribution)
            self.cr = self.chord_distribution['chord'][0]
            self.ct = self.chord_distribution['chord'][-1]
            self.taper = self.ct/self.cr

        elif callable(c):
            self.cr = c(0)
            self.ct = c(self.b)
            self.taper = self.ct/self.cr
            self.chord_distribution = self.__callable_input_allocation(c, self.b, 'chord', self.chord_distribution, self.__n_steps)

        elif ctype == dict:
            self.chord_distribution = self.__dictionary_input_allocation(c, 'chord', self.chord_distribution)
            self.cr = self.chord_distribution['chord'][0]
            self.ct = self.chord_distribution['chord'][0]
            self.taper = self.ct/self.cr

        else:
            raise TypeError("Invalid Input")

        # self.MAC = self.__calculate_MAC(self.chord_distribution['chord'])


    """
    Once all desired variables are defined, the wing will have to be 'assembled'. 
    Aka. The 3D coordinates will have to be calculated.
    """

    @staticmethod
    def __get_current_airfoil(airfoil_distribution: dict, yi: int or float, span: int or float):

        for foil, distr in airfoil_distribution.items():
            if distr[0] <= yi/span <= distr[1]:
                if foil[:4].lower() == 'naca':
                    if ' ' in foil:
                        code = foil.split(' ')[1]

                    else:
                        code = foil[4:]

                    if len(code) == 4:
                        coordinates = FourDigitNACA(code, 1).get_coordinates()

                    elif len(code) == 5:
                        coordinates = FiveDigitNACA(code, 1).get_coordinates()

                    else:
                        coordinates = LoadedAirfoil(foil, 1).load_coordinates()

                else:
                    coordinates = LoadedAirfoil(foil, 1).load_coordinates()

                return coordinates

        raise ValueError("Could not locate position along wing")

    def __create_initial_wing(self):

        data = {}

        for yi, ci in zip(self.__yrange, self.chord_distribution['chord']):
            data[yi] = self.__get_current_airfoil(self.airfoil_distribution, yi, self.b)
            data[yi]['x'] = data[yi]['x']*-ci
            data[yi]['z'] = data[yi]['z']*ci

        self.data_container.set_data(data)

    def __shift_wing_forward(self, percent_chord: float = 0.25):

        data = self.data_container.get_dictionary()

        for (yi, values), ci in zip(data.items(), self.chord_distribution['chord']):

            data[yi]['x'] += ci*percent_chord

        self.data_container.set_data(data)

    def __apply_twist(self):

        T = lambda theta: np.array([[np.cos(theta), -np.sin(theta)],
                                    [np.sin(theta), np.cos(theta)]])

        data = self.data_container.get_dictionary()

        for (yi, values), ti in zip(data.items(), self.twist_distribution['twist']):

            v = np.matmul(T(ti), np.array([values['x'], values['z']]))
            data[yi]['x'] = v[0, :]
            data[yi]['z'] = v[1, :]

        self.data_container.set_data(data)

    def __apply_sweep(self):
        pass

    def __apply_dihedral(self):
        pass

    def construct(self):

        self.__create_initial_wing()
        self.__shift_wing_forward(percent_chord=0.25)

        while self.transformation_order:
            self.transformation_order.pop()()

    @staticmethod
    def axisEqual3D(ax):
        """
        Taken from: https://stackoverflow.com/questions/8130823/set-matplotlib-3d-plot-aspect-ratio
        :param ax: fig.gca(projection='3d')
        """
        extents = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
        sz = extents[:, 1] - extents[:, 0]
        centers = np.mean(extents, axis=1)
        maxsize = max(abs(sz))
        r = maxsize / 2
        for ctr, dim in zip(centers, 'xyz'):
            getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)

    def plot_wing(self):

        fig = plt.figure()
        ax = fig.gca(projection='3d')
        arr = self.data_container.get_array()
        ax.scatter(arr[0, :], arr[1, :], arr[2, :], c='r', marker='o')

        ax.set_xlabel('X [m]')
        ax.set_ylabel('Y [m]')
        ax.set_zlabel('Z [m]')

        self.axisEqual3D(ax)


if __name__ == '__main__':

    testL = LoadedAirfoil('A63A108C')
    c = testL.load_coordinates()
    d = testL.spline_coordinate_calculation('cosine')

    W = Wing(20, n_steps=40)
    W.set_chord(lambda y: 3-2.7/20*y)
    W.set_dihedral(0)
    W.set_twist(0)
    W.set_sweep(0)
    W.set_airfoil('e1213')
    W.construct()
    W.plot_wing()
