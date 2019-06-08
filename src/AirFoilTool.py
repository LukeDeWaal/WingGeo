import numpy as np
from NumericalTools import derive
import matplotlib.pyplot as plt
import json


class NACAFoil(object):

    def __init__(self, code: str or int, n_digits: int, **kwargs):

        code = str(code)
        if len(code) != n_digits:
            raise ValueError(f"Expected a {n_digits}-Digit Input, got a {len(code)}-Digit input")
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
        self.__initialize_parameters()

        self.__yt = self.__thickness_distribution_functions()

        # If user defined custom values, they are assigned here
        if 'chord' in kwargs.keys():
            self.c = kwargs['chord'] if type(kwargs['chord']) in (int, float) else 1.0

    def __str__(self):
        return f"NACA-{self.code}"

    def __mul__(self, other: int or float):

        if type(other) not in [int, float]:
            raise TypeError(f"Cannot multiply with type {type(other)}, expected int or float")

        self.c *= other if other >= 0 else 1

    def __add__(self, other: int or float):

        if type(other) not in [int, float]:
            raise TypeError(f"Cannot add with type {type(other)}, expected int or float")

        self.c += other if other >= -self.c else 0

    def __initialize_parameters(self):

        self.__m = int(self.code[0]) / 100
        self.__p = int(self.code[1]) / 10
        self.__t = int(self.code[2:]) / 100

    def __thickness_distribution_functions(self):

        yt = lambda x: self.__t / 0.2 * (0.2969 * np.sqrt(x / self.c) -
                                         0.1260 * (x / self.c) -
                                         0.3515 * (x / self.c) ** 2 +
                                         0.2843 * (x / self.c) ** 3 -
                                         0.1015 * (x / self.c) ** 4) * self.c

        return yt

    @staticmethod
    def __theta_calculation(yc_p, yc_c):

        dyc_dx_p = derive(yc_p)
        dyc_dx_c = derive(yc_c)

        theta_p = lambda x: np.arctan(dyc_dx_p(x))
        theta_c = lambda x: np.arctan(dyc_dx_c(x))

        return theta_p, theta_c


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
        self.__yc_p, self.__yc_c = self.__mean_camber_line()
        self.__theta_p, self.__theta_c = self._NACAFoil__theta_calculation(self.__yc_p, self.__yc_c)

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


class FiveDigitNACA(NACAFoil):

    def __init__(self, code, **kwargs):

        # Initialize Parent NACA Class
        super().__init__(code=code, n_digits=5, **kwargs)



if __name__ == '__main__':

    test4d = FourDigitNACA('3210', chord=4)
    a = test4d.calculate_coordinates(cosine_spacing=True)

    test5d = FiveDigitNACA(23012, chord=1)

    inputs = {
        'a': 1,
        'c': 2,
        't': 3
    }


    plt.plot(a['XU'], a['YU'], 'ko')
    plt.plot(a['XL'], a['YL'], 'ko')
    plt.axis('equal')  # to preserve the aspect ratio of the plot
    plt.grid()
    plt.show()