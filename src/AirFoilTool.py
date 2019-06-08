import numpy as np
from NumericalTools import derive
import matplotlib.pyplot as plt
import json, os, sys


class NACAFoil(object):

    def __init__(self, code: str or int, n_digits: int, **kwargs):

        self.__n = n_digits

        code = str(code)
        if len(code) != self.__n:
            raise ValueError(f"Expected a {self.__n}-Digit Input, got a {len(code)}-Digit input")
        else:
            for char in code:
                if ord(char) < 48 or ord(char) > 57:
                    raise TypeError("Expected a numerical code, got characters instead")

        self.code = code

        # Chord of the airfoil
        self.c = 1.0

        # Plotting Parameters
        self.__m = None
        self.__p = None
        self.__t = None
        self.__k1 = None
        self.__initialize_parameters()

        # If user defined custom values, they are assigned here
        if 'chord' in kwargs.keys():
            self.c = kwargs['chord'] if type(kwargs['chord']) in (int, float) else 1.0

        self.__yt = self.__thickness_distribution_functions(self.__t, self.c)
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

        self.c *= other if other >= 0 else 1

    def __add__(self, other: int or float):
        """
        This will allow addition to be perfroemd on the object.
        The other number will be added to the chord and will adjust the thickness accordingly
        :param other: Number to add to chord. Cannot be smaller than current chord
        """

        if type(other) not in [int, float]:
            raise TypeError(f"Cannot add with type {type(other)}, expected int or float")

        self.c += other if other >= -self.c else 0

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

    def calculate_coordinates(self, cosine_spacing: bool = False, n: int = 50):

        data = {
            'XU': [],
            'YU': [],
            'XL': [],
            'YL': []
        }

        if cosine_spacing is False:
            xrange = np.linspace(0, self.c, n)

        elif cosine_spacing is True:
            xrange = 0.5*(1 - np.cos(np.linspace(0, np.pi, n)))*self.c

        else:
            raise ValueError(f"Expected a Boolean, got {type(cosine_spacing)} instead")

        for x in xrange:

            if x <= self.__p * self.c:
                data['XU'].append(x - self.__yt(x) * np.sin(self.__theta_p(x)))
                data['YU'].append(self.__yc_p(x) + self.__yt(x) * np.cos(self.__theta_p(x)))

                data['XL'].append(x + self.__yt(x) * np.sin(self.__theta_p(x)))
                data['YL'].append(self.__yc_p(x) - self.__yt(x) * np.cos(self.__theta_p(x)))

            elif self.c >= x > self.c * self.__p:
                data['XU'].append(x - self.__yt(x) * np.sin(self.__theta_c(x)))
                data['YU'].append(self.__yc_c(x) + self.__yt(x) * np.cos(self.__theta_c(x)))

                data['XL'].append(x + self.__yt(x) * np.sin(self.__theta_c(x)))
                data['YL'].append(self.__yc_c(x) - self.__yt(x) * np.cos(self.__theta_c(x)))

        return {key: np.array(value) for key, value in data.items()}


class FourDigitNACA(NACAFoil):

    def __init__(self, code: str or int, **kwargs):

        # Initialize Parent NACA Class
        super().__init__(code=code, n_digits=4, **kwargs)

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
            yc_0 = lambda x: self.__m / (self.__p ** 2) * (2 * self.__p * x / self.c - (x / self.c)** 2) * self.c
            yc_1 = lambda x: self.__m / ((1 - self.__p) ** 2) * (1 - 2 * self.__p + 2 * self.__p * x / self.c - (x / self.c) ** 2) * self.c

        elif self.__type == 'symmetrical':
            yc_0 = lambda x: 0
            yc_1 = lambda x: 0

        else:
            raise TypeError("Airfoil type not defined")

        return yc_0, yc_1


class FiveDigitNACA(NACAFoil):

    def __init__(self, code, **kwargs):

        # Initialize Parent NACA Class
        super().__init__(code=code, n_digits=5, **kwargs)

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



if __name__ == '__main__':

    test4d = FourDigitNACA('3210', chord=4)
    a = test4d.calculate_coordinates(cosine_spacing=True)

    test5d = FiveDigitNACA(23012, chord=1)
    b = test5d.calculate_coordinates(cosine_spacing=True)

    fig = plt.figure()
    plt.plot(a['XU'], a['YU'], 'ko')
    plt.plot(a['XL'], a['YL'], 'ko')
    plt.axis('equal')  # to preserve the aspect ratio of the plot
    plt.grid()
    plt.show()

    fig = plt.figure()
    plt.plot(b['XU'], b['YU'], 'ko')
    plt.plot(b['XL'], b['YL'], 'ko')
    plt.axis('equal')  # to preserve the aspect ratio of the plot
    plt.grid()
    plt.show()