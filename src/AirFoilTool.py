import numpy as np
from NumericalTools import derive


class NACAFoil(object):

    def __init__(self, code, **kwargs):

        code = str(code)
        if len(code) != 4:
            raise ValueError(f"Expected a 4-Digit Input, got a {len(code)}-Digit input")
        else:
            for char in code:
                if ord(char) < 48 or ord(char) > 57:
                    raise TypeError("Expected a 4-Digit Code, got characters instead")

        self.code = code

        # Step Size for Coordinate Calculations.
        self.dx = 0.0001    # Smaller will have higher accuracy but lower performance

        # Chord of the airfoil
        self.c = 1.0

        # If user defined custom values, they are assigned here
        if 'step' in kwargs.keys():
            self.dx = kwargs['step'] if type(kwargs['step']) in (int, float) else 0.0001

        if 'chord' in kwargs.keys():
            self.c = kwargs['chord'] if type(kwargs['chord']) in (int, float) else 1.0

        self.N = int(self.c/self.dx)

class FourDigitNACA(NACAFoil):

    def __init__(self, code: str or int, **kwargs):

        # Initialize Parent NACA Class
        super().__init__(code=code, **kwargs)

        self.__initialize_parameters()

        self.__yt = self.__thickness_distribution_functions()
        self.__yc_p, self.__yc_c = self.__mean_camber_line()
        self.__theta_p, self.__theta_c = self.__theta_calculation()

    def __str__(self):
        return f"NACA-{self.code}"

    def __initialize_parameters(self):

        self.__m = int(self.code[0]) / 100
        self.__p = int(self.code[1]) / 10
        self.__t = int(self.code[2:]) / 100

    def __thickness_distribution_functions(self):

        yt = lambda x: self.__t / 0.2 * (0.2969 * np.sqrt(x / self.c) -
                                         0.1260 * (x / self.c) -
                                         0.3515 * (x / self.c) ** 2 +
                                         0.2843 * (x / self.c) ** 3 -
                                         0.1015 * (x / self.c) ** 4)

        return yt

    def __mean_camber_line(self):

        yc_0 = lambda x: self.__m / (self.__p ** 2) * (2 * self.__p * x - x ** 2)
        yc_1 = lambda x: self.__m / ((1 - self.__p) ** 2) * (1 - 2 * self.__p + 2 * self.__p * x - x ** 2)

        return yc_0, yc_1

    def __theta_calculation(self):

        dyc_dx_p = derive(self.__yc_p)
        dyc_dx_c = derive(self.__yc_c)

        theta_p = lambda x: np.arctan(dyc_dx_p(x))
        theta_c = lambda x: np.arctan(dyc_dx_c(x))

        return theta_p, theta_c

    def calculate_coordinates(self, cosine_spacing: bool = False):

        data = {
            'XU': [],
            'YU': [],
            'XL': [],
            'YL': []
        }

        if cosine_spacing is False:
            xrange = np.linspace(0, self.c, self.N)

        elif cosine_spacing is True:
            xrange = 0.5*(1 - np.cos(np.linspace(0, np.pi, self.N)))*self.c

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


class FiveDigitNACA(object):

    def __init__(self):
        pass


if __name__ == '__main__':

    test = FourDigitNACA(4412)
    a = test.calculate_coordinates()