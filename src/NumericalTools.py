import numpy as np
import os


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

    return linear_function


def file_parser(rawdata_folder: str = r'C:\Users\lucky\Desktop\WingGeo\data\AirfoilCoordinates\raw',
                processed_folder: str = r'C:\Users\lucky\Desktop\WingGeo\data\AirfoilCoordinates\processed'):

    for datafile in os.listdir(rawdata_folder):
        print(f"Parsing {datafile}")

        for enc in ['utf-8', 'utf-16', 'iso-8859-15', 'cp437']:
            try:
                with open(rawdata_folder + '\\' + datafile, 'r', encoding=enc) as file:
                    lines = file.readlines()
                    if not ord(lines[0][0]) >= 48 and not ord(lines[0][0]) <= 57:
                        title = lines[0]
                        lines = lines[1:]
                    else:
                        title = None
                break

            except (UnicodeDecodeError, UnicodeError, UnicodeTranslateError):
                continue

        processed_lines = []

        for line in lines:
            while line[0] is ' ':
                line = line[1:]

            idx = line.find(' ')
            line = line[0:idx] + ',' + line[idx+1:]

            while line[idx+1] is ' ':
                line = line[0:idx+1] + line[idx+2:]

            processed_lines.append(line)

        with open(processed_folder + '\\' + datafile.split('.')[0] + '.txt', 'w+', encoding=enc) as file:
            file.write(''.join(processed_lines))


if __name__ == '__main__':

    file_parser()