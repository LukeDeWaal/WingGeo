import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d, Axes3D
from typing import Union
from backend.NumericalTools import linear_interpolation
from backend.AirFoilTool import FiveDigitNACA, FourDigitNACA, LoadedAirfoil


# TODO: Make discretization more modular


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
                self.__data_array[:, idx1*nxz + idx2] = np.array([x, y, z])

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

    def __init__(self):

        # Initialize all parameters defining the wing
        self.b = None
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
        self.__span_steps = 25
        self.__airfoil_steps = 25
        self.__cosine_spacing = False
        self.__yrange = None
        self.data_container = DataStorage()


    """
    Detail-Level Methods go below here
    """
    @staticmethod
    def __calculate_MAC(c: np.array):
        return np.average(c)

    def get_span(self):
        return self.b

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
    def __number_input_allocation(code: str, span_steps: Union[np.array, np.ndarray], key: str, target: dict or None, airfoil: bool = False):

        if target is None:
            target = dict()

        if airfoil is False:
            target['y'] = span_steps
            target[key] = np.array([code for _ in target['y']])

        elif airfoil is True:
            target[code] = (0, 1, None, None)

        return target

    @staticmethod
    def __array_input_allocation(array: list or np.array, span_steps: Union[np.array, np.ndarray], key: str, target: dict or None):

        # TODO: Interpolate the values of array to match discretization

        if target is None:
            target = {}

        if type(array) == list:
            array = np.array(array)

        new_array = []

        if array.shape[0] > array.shape[1]:
            for yi in span_steps:
                for i in range(len(array[:,1])-1):

                    if array[:,1][i+1] > yi >= array[:,1][i]:
                        new_array.append(linear_interpolation(yi, list(reversed(array[i, :])), list(reversed(array[i+1, :]))))

            target[key] = np.array(new_array)
            target["y"] = span_steps

        elif array.shape[0] < array.shape[1]:
            for yi in span_steps:
                for i in range(len(array[1, :]) - 1):

                    if array[1, :][i + 1] > yi >= array[1, :][i]:
                        new_array.append(linear_interpolation(yi, list(reversed(array[:, i])), list(reversed(array[:, i+1]))))

            target[key] = np.array(new_array)
            target["y"] = span_steps

        return target

    @staticmethod
    def __callable_input_allocation(function: callable, span_steps: Union[np.array, np.ndarray], key: str, target: dict or None):
        
        if target is None:
            target = {}

        target['y'] = span_steps
        target[key] = np.array([function(yi) for yi in target['y']])

        return target

    @staticmethod
    def __dictionary_input_allocation(dictionary: dict, span_steps: Union[np.array, np.ndarray], key: str, target: dict or None, airfoil=False):
        
        if target is None:
            target = {}

        if airfoil is False:
            target['y'] = span_steps
            target[key] = []

            keys = list(dictionary.keys())

            for yi in span_steps:
                for i in range(len(keys)-1):

                    if keys[i+1] > yi >= keys[i]:
                        target[key].append(linear_interpolation(yi, (keys[i], dictionary[keys[i]]), (keys[i+1], dictionary[keys[i+1]])))

            target[key] = np.array(target[key])

        elif airfoil is True:  # TODO: Airfoil transition morphing needs to be implemented

            for key_i, value in dictionary.items():
                target[key].append(value)

        return target

    """
    These methods will be used by the user to create their wing
    """
    def set_span_discretization(self, span_points: Union[list, np.array, np.ndarray]):

        self.b = span_points[-1]
        self.__yrange = np.array(span_points)

    def set_airfoil(self, airfoil: Union[str, dict]):
        
        airfoiltype = type(airfoil)

        if airfoiltype is str:
            self.airfoil_distribution = self.__number_input_allocation(airfoil, self.__yrange, 'airfoil', self.airfoil_distribution, airfoil=True)

        elif airfoiltype is dict:
            self.airfoil_distribution = self.__dictionary_input_allocation(airfoil, 'airfoil', self.airfoil_distribution, airfoil=True)

        else:
            raise TypeError("Invalid Input")
    
    def set_twist(self, twist: Union[int, float, callable, list, np.array, dict]):
        
        twisttype = type(twist)

        if twisttype in [int, float]:
            self.twist_distribution = self.__number_input_allocation(twist, self.__yrange, 'twist', self.twist_distribution)

        elif twisttype in [list, np.array]:
            self.twist_distribution = self.__array_input_allocation(twist, self.__yrange, 'twist', self.twist_distribution)

        elif callable(twist):
            self.twist_distribution = self.__callable_input_allocation(twist, self.__yrange, 'twist', self.twist_distribution)

        elif twisttype is dict:
            self.twist_distribution = self.__dictionary_input_allocation(twist, 'twist', self.twist_distribution)

        else:
            raise TypeError("Invalid Input")

        self.transformation_order.append(self.__apply_twist)
    
    def set_dihedral(self, dihedral: Union[int, float, callable, list, np.array, dict]):
        
        dihedraltype = type(dihedral)
        
        if dihedraltype in [int, float]:
            self.dihedral_distribution = self.__number_input_allocation(dihedral, self.__yrange, 'dihedral', self.dihedral_distribution)

        elif dihedraltype in [list, np.array]:
            self.dihedral_distribution = self.__array_input_allocation(dihedral, self.__yrange, 'dihedral', self.dihedral_distribution)

        elif callable(dihedral):
            self.dihedral_distribution = self.__callable_input_allocation(dihedral, self.__yrange, 'dihedral', self.dihedral_distribution)

        elif dihedraltype is dict:
            self.dihedral_distribution = self.__dictionary_input_allocation(dihedral, 'dihedral', self.dihedral_distribution, )

        else:
            raise TypeError("Invalid Input")

        self.transformation_order.append(self.__apply_dihedral)
        
    def set_sweep(self, sweep: Union[int, float, callable, list, np.array, dict]):

        sweeptype = type(sweep)
    
        if sweeptype in [int, float]:
            self.sweep_distribution = self.__number_input_allocation(sweep, self.__yrange, 'sweep', self.sweep_distribution)

        elif sweeptype in [list, np.array]:
            self.sweep_distribution = self.__array_input_allocation(sweep, self.__yrange, 'sweep', self.sweep_distribution)

        elif callable(sweep):
            self.sweep_distribution = self.__callable_input_allocation(sweep, self.__yrange, 'sweep', self.sweep_distribution)
            
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
            self.chord_distribution = self.__number_input_allocation(c, self.__yrange, 'chord', self.chord_distribution)

        elif ctype in [list, np.array]:

            self.chord_distribution = self.__array_input_allocation(c, self.__yrange, 'chord', self.chord_distribution)
            self.cr = self.chord_distribution['chord'][0]
            self.ct = self.chord_distribution['chord'][-1]
            self.taper = self.ct/self.cr

        elif callable(c):
            self.cr = c(0)
            self.ct = c(self.b)
            self.taper = self.ct/self.cr
            self.chord_distribution = self.__callable_input_allocation(c, self.__yrange, 'chord', self.chord_distribution)

        elif ctype == dict:
            self.chord_distribution = self.__dictionary_input_allocation(c, 'chord', self.chord_distribution)
            self.cr = self.chord_distribution['chord'][0]
            self.ct = self.chord_distribution['chord'][0]
            self.taper = self.ct/self.cr

        else:
            raise TypeError("Invalid Input")

        # self.MAC = self.__calculate_MAC(self.chord_distribution['chord'])

    def set_spanwise_steps(self, n_steps: int):
        self.__span_steps = n_steps

    def set_airfoil_steps(self, n_steps: int):
        self.__airfoil_steps = n_steps

    def set_cosine_spacing(self, b: bool):
        self.__cosine_spacing = b

    """
    Once all desired variables are defined, the wing will have to be 'assembled'. 
    Aka. The 3D coordinates will have to be calculated.
    """

    @staticmethod
    def __get_current_airfoil(airfoil_distribution: dict, yi: int or float, span: int or float, steps: int, cosine_spacing: bool):

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
                        coordinates = LoadedAirfoil(foil, 1).load_coordinates(cosine_spacing=cosine_spacing, n=steps)

                else:
                    coordinates = LoadedAirfoil(foil, 1).load_coordinates(cosine_spacing=cosine_spacing, n=steps)

                return coordinates

        raise ValueError("Could not locate position along wing")

    def __create_initial_wing(self):

        data = {}

        for yi, ci in zip(self.__yrange, self.chord_distribution['chord']):
            data[yi] = self.__get_current_airfoil(self.airfoil_distribution, yi, self.b, cosine_spacing=self.__cosine_spacing, steps=self.__airfoil_steps)
            data[yi]['x'] = data[yi]['x']*-ci
            data[yi]['z'] = data[yi]['z']*ci

        self.data_container.set_data(data)

    def __shift_wing_horizontally(self, percent_chord: float = 0.25):

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

        data = self.data_container.get_dictionary()
        delta_x = 0

        keys = list(data.keys())

        for (idx, key), alpha in zip(enumerate(keys[:-1]), self.sweep_distribution['sweep']):

            delta_x = delta_x + (keys[idx+1] - key)*np.tan(alpha)

            data[keys[idx+1]]['x'] -= delta_x

        self.data_container.set_data(data)

    def __apply_dihedral(self):

        data = self.data_container.get_dictionary()
        delta_z = 0

        keys = list(data.keys())

        for (idx, key), alpha in zip(enumerate(keys[:-1]), self.dihedral_distribution['dihedral']):
            delta_z = delta_z + (keys[idx + 1] - key) * np.tan(alpha)

            data[keys[idx + 1]]['z'] += delta_z

        self.data_container.set_data(data)

    def construct(self):

        self.__create_initial_wing()
        self.__shift_wing_horizontally(percent_chord=0.25)

        # while self.transformation_order:
        #     self.transformation_order.pop()()

        # self.__shift_wing_horizontally(percent_chord=-0.25)

    @staticmethod
    def axisEqual3D(ax):
        """
        Taken from: https://stackoverflow.com/questions/8130823/set-matplotlib-3d-plot-aspect-ratio
        All credits for this method go to the original author.
        :param ax: fig.gca(projection='3d')
        """
        extents = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
        sz = extents[:, 1] - extents[:, 0]
        centers = np.mean(extents, axis=1)
        maxsize = max(abs(sz))
        r = maxsize / 2
        for ctr, dim in zip(centers, 'xyz'):
            getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)

    def plot_wing(self, fig=None):

        fig = plt.figure() if fig is None else fig
        ax = fig.add_subplot(111, projection='3d')
        arr = self.data_container.get_array()
        ax.scatter(arr[0, :], arr[1, :], arr[2, :], c='r', marker='o')

        ax.set_xlabel('X [m]')
        ax.set_ylabel('Y [m]')
        ax.set_zlabel('Z [m]')

        self.axisEqual3D(ax)


if __name__ == '__main__':

    W = Wing()
    W.set_span_discretization(list(np.linspace(0, 20, 30))+list(np.linspace(20.1, 30, 30)))
    W.set_chord(lambda y: 3*np.sqrt(1-(y**2)/(W.b**2)))
    W.set_sweep(lambda y: 1-y/(W.b/3) if y < W.b/3 else (0 if y < 2*W.b/3 else 0.3))
    W.set_dihedral(lambda y: y/W.b*0.5)
    W.set_twist(lambda y: 0.1-0.1*y/W.b)
    W.set_airfoil('e1213')
    W.construct()
    W.plot_wing()
