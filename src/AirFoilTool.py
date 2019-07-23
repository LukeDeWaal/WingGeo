import numpy as np
from NumericalTools import derive
import matplotlib.pyplot as plt
import json, os, sys
import pandas as pd
from scipy import interpolate
from typing import Union

if sys.platform == 'win32':
    datafiles_path = '\\'.join(os.getcwd().split('\\')[:-1]) + '\\data\\AirfoilCoordinates\\processed'

else:
    datafiles_path = '/'.join(os.getcwd().split('/')[:-1]) + 'data/AirfoilCoordinates/processed'

AIRFOILS = [file.split('.')[0] for file in os.listdir(datafiles_path)]


class AirFoil(object):

    def __init__(self, chord: int or float):

        self.chord = chord
        self.coordinates = None

    @staticmethod
    def __turning_point(arr):

        oldval = arr[0]
        for idx, value in enumerate(arr[1:]):
            if value > oldval:
                return idx

            else:
                oldval = float(value)

        raise ValueError("Could not find turning point in given arrays. "
                         "Make sure the coordinates are defined from upper trailing edge to lower trailing edge.")

    def __find_turning_point(self):

        x = self.coordinates['x']

        return self.__turning_point(x)

    def spline_coordinate_calculation(self, xnew: Union[list, np.array, str], k: int = 3, s: int = 0, **kwargs):

        arrsort = lambda xarr, zarr: np.array(
            [[xi, zi] for xi, zi in sorted(zip(xarr, zarr),
                                           key=lambda pair:
                                           pair[0])
             ]
        )

        if type(xnew) == list:
            xnew = np.array(xnew)

        elif type(xnew) == str:

            if 'n' not in kwargs.keys():
                kwargs['n'] = 50

            xnew = xnew.lower()
            if xnew == 'uniform' or xnew == 'linear':
                xnew = np.concatenate((np.linspace(1, 0, kwargs['n']), np.linspace(0, 1, kwargs['n'])))

            elif xnew == 'cosine_spacing' or xnew == 'cosinespacing' or xnew == 'cosine':
                cosine = 0.5 * (1 - np.cos(np.linspace(0, np.pi, kwargs['n']))) * self.chord
                xnew = np.concatenate((cosine[::-1], cosine))

        idx_t_old = self.__find_turning_point()
        idx_t_new = self.__turning_point(xnew)

        upper_coordinates = arrsort(self.coordinates['x'][:idx_t_old], self.coordinates['z'][:idx_t_old])
        lower_coordinates = arrsort(self.coordinates['x'][idx_t_old:], self.coordinates['z'][idx_t_old:])

        tU, cU, kU = interpolate.splrep(upper_coordinates[:, 0], upper_coordinates[:, 1], k=k, s=s)
        tL, cL, kL = interpolate.splrep(lower_coordinates[:, 0], lower_coordinates[:, 1], k=k, s=s)

        upper_spline = interpolate.BSpline(tU, cU, kU, extrapolate=False)
        lower_spline = interpolate.BSpline(tL, cL, kL, extrapolate=False)

        self.coordinates = {
            'x': xnew,
            'z': np.concatenate((upper_spline(xnew[:idx_t_new]), lower_spline(xnew[idx_t_new:])))
        }

        return self.coordinates


class NACAFoil(AirFoil):

    def __init__(self, code: str or int, n_digits: int, chord: int or float, **kwargs):

        super().__init__(chord=chord)

        self.__n = n_digits

        code = str(code)
        if len(code) != self.__n:
            raise ValueError(f"Expected a {self.__n}-Digit Input, got a {len(code)}-Digit input")
        else:
            for char in code:
                if ord(char) < 48 or ord(char) > 57:
                    raise TypeError("Expected a numerical code, got characters instead")

        self.code = code

        # Plotting Parameters
        self.__m = None
        self.__p = None
        self.__t = None
        self.__k1 = None
        self.__initialize_parameters()

        # Plotting Functions
        self.__yt = self.__thickness_distribution_functions(self.__t, self.chord)
        self.__yc_p = lambda: None
        self.__yc_c = lambda: None
        self.__theta_p = lambda: None
        self.__theta_c = lambda: None

    def __str__(self):
        """
        Method to support printing the object in console
        """
        return f"NACA-{self.code}"

    def __mul__(self, other: int or float):
        """
        This will allow multiplication with the object.
        This will multiply the chord with the other and adjust the thickness accordingly
        :param other: Factor with which to multiply the object. Can only be positive non-zero numbers.
        """

        if type(other) not in [int, float]:
            raise TypeError(f"Cannot multiply with type {type(other)}, expected int or float")

        self.chord *= other if other >= 0 else 1

    def __add__(self, other: int or float):
        """
        This will allow addition to be perfroemd on the object.
        The other number will be added to the chord and will adjust the thickness accordingly
        :param other: Number to add to chord. Cannot be smaller than current chord
        """

        if type(other) not in [int, float]:
            raise TypeError(f"Cannot add with type {type(other)}, expected int or float")

        self.chord += other if other >= -self.chord else 0

    def __initialize_parameters(self):
        """
        Will initialize the parameters used to describe the geometry for the airfoils.
        """

        if self.__n == 4:
            self.__m = int(self.code[0]) / 100   # Maximum camber
            self.__p = int(self.code[1]) / 10    # Position of maximum camber
            self.__t = int(self.code[2:]) / 100  # Maximum thickness

        elif self.__n == 5:

            if sys.platform == 'win32':
                datafile = '\\'.join(os.getcwd().split('\\')[:-1])+'\\data\\fivedigit_coefficients.json'

            else:
                datafile = '/'.join(os.getcwd().split('/')[:-1]) + 'data/fivedigit_coefficients.json'

            with open(datafile, 'r') as file:
                coefficients = json.load(file)[self.code[0:3]]

            self.__m = coefficients['m']         # Camber function parameter
            self.__p = coefficients['p']         # Position of Maximum Camber
            self.__k1 = coefficients['k1']       # Camber function parameter
            self.__t = int(self.code[3:]) / 100  # Maximum thickness

    @staticmethod
    def __thickness_distribution_functions(t, c):
        """
        Method to calculate the thickness distribution for the airfoil. Is identical for 4- and 5-digit airfoils.
        :param t: thickness value
        :param c: chordlength
        :return: function with as input a number from 0 to c and returning airfoil thickness.
        """

        yt = lambda x: t / 0.2 * (0.2969 * np.sqrt(x / c) -
                                         0.1260 * (x / c) -
                                         0.3515 * (x / c) ** 2 +
                                         0.2843 * (x / c) ** 3 -
                                         0.1015 * (x / c) ** 4) * c

        return yt

    @staticmethod
    def __modified_thickness_distribution():
        pass

    # TODO: Implement modified thickness functions
    # TODO: Finish copying coefficients for modified 20% thickness airfoils

    @staticmethod
    def __theta_calculation(yc_p, yc_c):
        """
        Method to calculate the slope of the airfoil. Is identical for 4- and 5-digit airfoils.
        :param yc_p: Function describing the camberline with as input a number from 0 to p
        :param yc_c:
        :return:
        """

        dyc_dx_p = derive(yc_p)
        dyc_dx_c = derive(yc_c)

        theta_p = lambda x: np.arctan(dyc_dx_p(x))
        theta_c = lambda x: np.arctan(dyc_dx_c(x))

        return theta_p, theta_c

    def get_coordinates(self):
        return self.coordinates

    def load_coordinates(self, cosine_spacing: bool = False, n: int = 25):

        data = {
            'XU': [],
            'YU': [],
            'XL': [],
            'YL': []
        }

        if cosine_spacing is False:
            xrange = np.linspace(0, self.chord, n)

        elif cosine_spacing is True:
            xrange = 0.5*(1 - np.cos(np.linspace(0, np.pi, n)))*self.chord

        else:
            raise ValueError(f"Expected a Boolean, got {type(cosine_spacing)} instead")

        for x in xrange:

            if x <= self.__p * self.chord:
                data['XU'].append(x - self.__yt(x) * np.sin(self.__theta_p(x)))
                data['YU'].append(self.__yc_p(x) + self.__yt(x) * np.cos(self.__theta_p(x)))

                data['XL'].append(x + self.__yt(x) * np.sin(self.__theta_p(x)))
                data['YL'].append(self.__yc_p(x) - self.__yt(x) * np.cos(self.__theta_p(x)))

            elif self.chord >= x > self.chord * self.__p:
                data['XU'].append(x - self.__yt(x) * np.sin(self.__theta_c(x)))
                data['YU'].append(self.__yc_c(x) + self.__yt(x) * np.cos(self.__theta_c(x)))

                data['XL'].append(x + self.__yt(x) * np.sin(self.__theta_c(x)))
                data['YL'].append(self.__yc_c(x) - self.__yt(x) * np.cos(self.__theta_c(x)))

        x = np.concatenate((data['XU'][::-1], data['XL']))
        z = np.concatenate((data['YU'][::-1], data['YL']))

        self.coordinates = {"x": x, "z": z}

        return self.coordinates


class FourDigitNACA(NACAFoil):

    def __init__(self, code: str or int, chord: int or float, **kwargs):

        # Initialize Parent NACA Class
        super().__init__(code=code, chord=chord, n_digits=4, **kwargs)

        self.__p = self._NACAFoil__p
        self.__m = self._NACAFoil__m

        if self.__p == 0 and self.__m == 0:
            self.__type = 'symmetrical'

        else:
            self.__type = 'cambered'

        self.__yt = self._NACAFoil__yt
        self._NACAFoil__yc_p, self._NACAFoil__yc_c = self.__mean_camber_line()
        self._NACAFoil__theta_p, self._NACAFoil__theta_c = self._NACAFoil__theta_calculation(self._NACAFoil__yc_p, self._NACAFoil__yc_c)

    def __mean_camber_line(self):

        if self.__type == 'cambered':
            yc_0 = lambda x: self.__m / (self.__p ** 2) * (2 * self.__p * x / self.chord - (x / self.chord) ** 2) * self.chord
            yc_1 = lambda x: self.__m / ((1 - self.__p) ** 2) * (1 - 2 * self.__p + 2 * self.__p * x / self.chord - (x / self.chord) ** 2) * self.chord

        elif self.__type == 'symmetrical':
            yc_0 = lambda x: 0
            yc_1 = lambda x: 0

        else:
            raise TypeError("Airfoil type not defined")

        return yc_0, yc_1


class FiveDigitNACA(NACAFoil):

    def __init__(self, code: str or int, chord: int or float, **kwargs):

        # Initialize Parent NACA Class
        super().__init__(code=code, chord=chord, n_digits=5, **kwargs)

        self.__p = self._NACAFoil__p
        self.__m = self._NACAFoil__m
        self.__k1 = self._NACAFoil__k1

        self.__yt = self._NACAFoil__yt
        self._NACAFoil__yc_p, self._NACAFoil__yc_c = self.__mean_camber_line()
        self._NACAFoil__theta_p, self._NACAFoil__theta_c = self._NACAFoil__theta_calculation(self._NACAFoil__yc_p,
                                                                                             self._NACAFoil__yc_c)

    def __mean_camber_line(self):

        yc_0 = lambda x: self.__k1/6*(x**3 - 3*self.__m*x**2+self.__m**2*(3-self.__m)*x)
        yc_1 = lambda x: self.__k1/6*self.__m**3*(1-x)

        return yc_0, yc_1


class LoadedAirfoil(AirFoil):

    def __init__(self, code: str, chord: int or float = 1.0):

        super().__init__(chord=chord)

        self.code = code.lower()

    def load_coordinates(self, cosine_spacing: bool = False, n: int = 25):

        self.coordinates = self.__load_airfoil()

        if cosine_spacing is False:
            xrange = 'linear'

        elif cosine_spacing is True:
            xrange = 'cosine'

        # self.coordinates = self.spline_coordinate_calculation(xrange)

        return self.spline_coordinate_calculation(xrange, n=n)

    def __load_airfoil(self):

        if sys.platform == 'win32':
            datafiles_path = '\\'.join(os.getcwd().split('\\')[:-1]) + '\\data\\AirfoilCoordinates\\processed'

        else:
            datafiles_path = '/'.join(os.getcwd().split('/')[:-1]) + 'data/AirfoilCoordinates/processed'

        airfoils = AIRFOILS

        print(self.code)
        if self.code not in airfoils:
            raise ValueError("Specified Airfoil not found in database")

        else:
            coordinates = pd.read_csv(datafiles_path+f"\\{self.code}.txt",
                                      sep=',',
                                      index_col=False,
                                      skiprows=[0],
                                      header=None,
                                      names=['x', 'z'],
                                      dtype=float)

        return {"x": np.array(coordinates['x'], dtype=float),
                "z": np.array(coordinates['z'], dtype=float)}


if __name__ == '__main__':

    test4d = FourDigitNACA('3210', chord=4)
    a = test4d.load_coordinates(cosine_spacing=True)

    test5d = FiveDigitNACA(23012, chord=1)
    b = test5d.load_coordinates(cosine_spacing=True)

    testL = LoadedAirfoil('e1213')
    c = testL.load_coordinates(cosine_spacing=True)

    fig = plt.figure()
    plt.plot(a['x'], a['z'], 'ko')
    plt.axis('equal')  # to preserve the aspect ratio of the plot
    plt.grid()
    plt.show()

    fig = plt.figure()
    plt.plot(b['x'], b['z'], 'ko')
    plt.axis('equal')  # to preserve the aspect ratio of the plot
    plt.grid()
    plt.show()

    fig = plt.figure()
    plt.plot(c['x'], c['z'], 'ko')
    plt.axis('equal')  # to preserve the aspect ratio of the plot
    plt.grid()
    plt.show()