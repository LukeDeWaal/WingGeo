import matplotlib
matplotlib.use("TkAgg")
from mpl_toolkits.mplot3d import axes3d, Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseEvent
import matplotlib.animation as animation
# from matplotlib import style
# style.use('ggplot')

import numpy as np
import math
import tkinter as tk
from tkinter import ttk
import ttkwidgets as ttkw

from backend.WingTool import Wing
from frontend.TkTable import Tk_Table


LARGE_FONT = ("Verdana", 12)
ROOT_GEO = f"{700}x{600}+{200}+{200}"
EDITOR_GEO = f"{300}x{500}+{900}+{200}"


class Error(Exception):
   """
   Base class for other exceptions
   """
   pass


class InvalidUserInputError(Error):
    """
    Raised when user inputs something erroneous
    """
    pass


# TODO: Create editors
class EditorWindow(tk.Toplevel):

    def __init__(self, root, name):

        super().__init__(root)
        self.name = name
        self.title(self.name)

        self.menubar = tk.Menu(self.master)
        self.config(menu=self.menubar)

        # File Menu
        fileMenu = tk.Menu(self.menubar)
        fileMenu.config(tearoff=False)
        fileMenu.add_command(label="New", command=lambda: None)
        fileMenu.add_command(label="Open", command=lambda: None)
        fileMenu.add_command(label="Save", command=lambda: self.__save())
        fileMenu.add_command(label="Exit", command=lambda: self.wm_withdraw())
        self.menubar.add_cascade(label="File", menu=fileMenu)

        self.btn_frame = tk.Frame(self)
        self.btn_frame.grid(
            row=0, column=0, sticky='nw'
        )

        self.btn_frame.grid_rowconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)
        self.btn_frame.grid_columnconfigure(2, weight=1)
        self.btn_frame.grid_columnconfigure(3, weight=1)
        self.btn_frame.grid_columnconfigure(4, weight=1)

        self.apply_btn = ttk.Button(
            self.btn_frame,
            text='Update',
            command=lambda: self.table_to_plot()
        )
        self.apply_btn.grid(
            row=0,
            column=0,
            sticky='n',
        )

        def add_row():
            idx = self.table.indices_of_selected_rows[-1]
            self.table.insert_row(
                [self.table[(idx, 1)], self.table[(idx, 1)], 10],
                idx+1
            )
            self.table_to_plot()

        def del_row():
            self.table.delete_all_selected_rows()
            self.table_to_plot()

        self.add_btn = ttk.Button(
            self.btn_frame,
            text='Add Row',
            command=lambda: add_row()
        )
        self.add_btn.grid(
            row=0,
            column=1,
            sticky='n',
        )

        self.reset_btn = ttk.Button(
            self.btn_frame,
            text='Reset',
            command=lambda: self.__reset()
        )
        self.reset_btn.grid(
            row=0,
            column=2,
            sticky='n',
        )

        self.clear_btn = ttk.Button(
            self.btn_frame,
            text='Delete',
            command=lambda: del_row()
        )
        self.clear_btn.grid(
            row=0,
            column=3,
            sticky='n',
        )

        self.entry_frame = tk.Frame(self)
        self.entry_frame.grid(
            row=1, column=0, sticky='nw'
        )

        if self.name == 'Span Distr.':
            cols = ['Start', 'Stop', 'Steps']

        else:
            cols = ['Start', 'Stop', self.name]

        self.table = Tk_Table(
            self.entry_frame,
            cols,
            height=30
        )

        self.standard_inputs = {
            'Span Distr.': 10,
            'Chord': 1,
            'Twist': 0,
            'Sweep': 0,
            'Dihedral': 0,
            'Airfoils': 'NACA0012'
        }

        self.plot_limits = {
            'Span Distr.': (0, 100),
            'Chord': (0, 10),
            'Twist': (-np.pi/2, np.pi/2),
            'Sweep': (-np.pi/2, np.pi/2),
            'Dihedral': (-np.pi/2, np.pi/2),
            'Airfoils': 'NACA0012'
        }

        self.output_type = int if self.name == 'Span Distr.' else str if self.name == 'Airfoils' else lambda x: round(float(x), 3)

        self.table.insert_row([0, float(self.get_span()), self.standard_inputs[self.name]], 0)

        self.table.grid(
            row=0,
            column=0,
            sticky='nw'
        )

        self.plotting_frame = tk.Frame(self)
        self.plotting_frame.grid(row=1, column=1, sticky='nw')

        self._figure, self.plot, self._line, self._ranges = None, None, None, {}
        self._dragging_point = None
        self._points = {}

        self.xlim = (0, float(self.get_span()))
        self.ylim = self.plot_limits[self.name]

        self._figure = Figure(figsize=(5, 5), dpi=100)

        canvas = FigureCanvasTkAgg(self._figure, self.plotting_frame)
        canvas.draw()

        self.plot = self._figure.subplots(1, 1)
        self.plot.grid()
        self.plot.set_facecolor((0.9, 0.9, 0.9))

        toolbar = NavigationToolbar2Tk(canvas, self.plotting_frame)
        toolbar.update()

        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self._init_plot()

        self.last_edited = 'plot'
        self.bind('<Return>', self.__update_table_and_plot)

    def __create_distribution(self):

        points = list(self._points.items())
        r = []
        for idx in range(len(points)-1):
            d = points[idx+1][0] - points[idx][0]
            r += list(np.arange(points[idx][0], points[idx][1], d/points[idx][1]))

        self.master.discretization = np.array(r)
        self.master.entry_box_change()

    def __update_table_and_plot(self, event):

        if len(self.table.selected_rows) > 0:
            self.table.deselect_all()
            self.table_to_plot()
        else:
            pass

    def get_span(self):
        return self.master.parameter_variables['Span'].get()

    def __reset(self):

        self.table.deselect_all()
        [self.table.select_row(i) for i in range(self.table.number_of_rows)]
        self.table.delete_all_selected_rows()

        self.table.insert_row([0.0, float(self.get_span()), self.standard_inputs[self.name]], 0)
        self.table_to_plot()

    def __open(self):
        pass

    def __save(self):
        self.__create_distribution()

    def __new(self):
        pass

    def table_to_plot(self):

        self._points = {}

        for i in range(self.table.number_of_rows):
            point = (float(self.table[(i, 0)]), self.output_type(self.table[(i, 2)]))
            self._add_point(*point)

        self._add_point(float(self.table[(i, 1)]), self.output_type(self.table[(i, 2)]))
        self.update_plot()

    def plot_to_table(self):

        for i in range(self.table.number_of_rows):
            self.table.select_row(i)

        self.table.delete_all_selected_rows()

        xs = list(self._points.keys())
        ys = list(self._points.values())

        xy = zip(xs, ys)

        sxy = sorted(xy)
        xsort = []
        ysort = []

        for x, y in sxy:
            xsort.append(x)
            ysort.append(y)

        for idx in range(len(xsort)-1):
            self.table.insert_row([round(xsort[idx], 3), round(xsort[idx+1], 3), self.output_type(ysort[idx])])

        self.table.sort_by(0, False)

    def _init_plot(self):

        self.plot.set_xlim(*self.xlim)
        self.plot.set_ylim(*self.ylim)
        self.plot.grid(which="both")

        self._figure.canvas.mpl_connect('button_press_event', self._on_click)
        self._figure.canvas.mpl_connect('button_release_event', self._on_release)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_motion)

        self._add_point(0, self.standard_inputs[self.name])
        self._add_point(float(self.get_span()), self.standard_inputs[self.name])
        self.update_plot()

    def _update_plot_limits(self):
        self.xlim = (0, float(self.get_span()))
        self.plot.set_xlim(*self.xlim)

    def update_plot(self):

        self._update_plot_limits()

        if not self._points:
            self._line.set_data([], [])
        else:
            x, y = zip(*sorted(self._points.items()))
            x = list(x)
            y = list(y)

            x[0] = 0
            x[-1] = float(self.get_span())
            y[-1] = y[-2]

            self._points = {xi: yi for xi, yi in zip(x, y)}

            x, y = zip(*sorted(self._points.items()))
            x = list(x)
            y = list(y)

            # Add new plot
            if not self._line:
                self._line, = self.plot.plot(x, y, "rx-", markersize=10)

            # Update current plot
            else:
                self._line.set_data(x, y)

            # for idx in range(len(x)-1):
            #     self._line.set_data(np.linspace(x[idx], x[idx+1], 10), np.ones((10,))*y[idx])

        self._figure.canvas.draw()
        self.plot_to_table()

    def _add_point(self, x, y=None):
        if isinstance(x, MouseEvent):
            x, y = float(x.xdata), float(x.ydata)
        self._points[x] = y

        return x, y

    def _remove_point(self, x, y):
        if x in self._points.keys() and y in self._points.values():
            self._points.pop(x)

    def _find_neighbor_point(self, event):
        u""" Find point around mouse position
        :rtype: ((int, int)|None)
        :return: (x, y) if there are any point around mouse else None
        """
        distance_threshold = 3.0
        nearest_point = None
        min_distance = float('inf')
        for x, y in self._points.items():
            distance = math.hypot(event.xdata - x, event.ydata - y)
            if distance < min_distance:
                min_distance = distance
                nearest_point = (x, y)
        if min_distance < distance_threshold:
            return nearest_point
        return None

    def _on_click(self, event):
        u""" callback method for mouse click event
        :type event: MouseEvent
        """
        # left click
        if event.button == 1 and event.inaxes in [self.plot]:
            point = self._find_neighbor_point(event)
            if point:
                self._dragging_point = point
            else:
                self._add_point(event)
            self.update_plot()
        # right click
        elif event.button == 3 and event.inaxes in [self.plot]:
            point = self._find_neighbor_point(event)
            if point:
                self._remove_point(*point)
                self.update_plot()

    def _on_release(self, event):
        u""" callback method for mouse release event
        :type event: MouseEvent
        """
        if event.button == 1 and event.inaxes in [self.plot] and self._dragging_point:
            self._dragging_point = None
            self.update_plot()

    def _on_motion(self, event):
        u""" callback method for mouse motion event
        :type event: MouseEvent
        """
        if not self._dragging_point:
            return
        if event.xdata is None or event.ydata is None:
            return

        self._remove_point(*self._dragging_point)

        if event.xdata > 0:
            pass

        else:
            event.xdata = 0

        self._dragging_point = self._add_point(event)
        self.update_plot()


class WingEditor(tk.Tk):

    def __init__(self, *args, **kwargs):

        # Backend Initialization
        self.wing = Wing()
        self.wing.set_span_discretization(np.linspace(0, 10, 21))
        self.wing.set_chord(lambda y: 3*np.sqrt(1-(y**2)/(self.wing.b**2)))
        self.wing.set_twist(0)
        self.wing.set_airfoil('e1213')
        self.wing.set_dihedral(0.1)
        self.wing.set_sweep(0)
        self.wing.construct()

        # Setting up Frontend
        super().__init__(*args, **kwargs)
        tk.Tk.wm_title(self, "WingGeo Editor")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=10)
        self.grid_columnconfigure(1, weight=10)
        self.grid_columnconfigure(2, weight=2)

        # Menu Bar Creation
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        # File Menu
        fileMenu = tk.Menu(self.menubar)
        fileMenu.config(tearoff=False)
        fileMenu.add_command(label="Exit", command=lambda: self.quit())
        self.menubar.add_cascade(label="File", menu=fileMenu)

        # 3D Plot
        self.plot3d_container = tk.Frame(self)
        self.plot3d_container.grid_columnconfigure(0, weight=1)
        self.plot3d_container.grid_rowconfigure(0, weight=1)
        self.plot3d_container.grid(row=0, column=0, sticky='NSEW')

        self.fig_3d = Figure(figsize=(5, 5), dpi=100)

        canvas3d = FigureCanvasTkAgg(self.fig_3d, self.plot3d_container)
        canvas3d.draw()

        self.plot3d = self.fig_3d.add_subplot(111, projection="3d")

        toolbar = NavigationToolbar2Tk(canvas3d, self.plot3d_container)
        toolbar.update()
        canvas3d._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas3d.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # 2D Plot Creation
        self.plot2d_container = tk.Frame(self)
        self.plot2d_container.grid_columnconfigure(0, weight=10)
        self.plot2d_container.grid_columnconfigure(1, weight=1)
        self.plot2d_container.grid_rowconfigure(0, weight=1)
        self.plot2d_container.grid(
            row=0,
            column=1,
            sticky='NSEW'
        )

        self.fig_2d = Figure(figsize=(5, 5), dpi=100)

        canvas2d = FigureCanvasTkAgg(self.fig_2d, self.plot2d_container)
        canvas2d.draw()

        self.plots2d = {}
        self.top_plot2d = self.fig_2d.add_subplot(311)
        self.front_plot2d = self.fig_2d.add_subplot(312, sharex=self.top_plot2d)
        self.side_plot2d = self.fig_2d.add_subplot(313)

        self.plots2d['topdown']   = self.top_plot2d
        self.plots2d['front'] = self.front_plot2d
        self.plots2d['side']  = self.side_plot2d

        for key, plot in self.plots2d.items():
            plot.grid()

        toolbar = NavigationToolbar2Tk(canvas2d, self.plot2d_container)
        toolbar.update()
        canvas2d._tkcanvas.pack(
            side=tk.TOP,
            fill=tk.BOTH,
            expand=True
        )

        # Slider
        self.button_frame = tk.Frame(self)
        nrows = 3
        for row in range(nrows):
            self.button_frame.grid_rowconfigure(row, weight=1)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid(
            row=0,
            column=2,
            sticky='NSEW'
        )

        self.span_slider = ttkw.TickScale(
            self.button_frame,
            from_=0,
            to=10,
            tickinterval=8,
            orient=tk.VERTICAL
            # resolution=0.2
        )
        self.span_slider.grid(
            row=2,
            column=1,
            sticky='NSEW'
        )

        self.display = tk.Label(
            self.button_frame,
            text=str(round(self.span_slider.get(), 4))
        )
        self.display.grid(
            row=1,
            column=0,
            sticky='S'
        )

        self.parameter_label_texts = [
            'Span',
            'Airfoil Steps',
            'Span Distr.',
            'Airfoils',
            'Chord',
            'Sweep',
            'Twist',
            'Dihedral',
        ]

        # Finally
        self.__plot()
        #self.animation_3d = animation.FuncAnimation(self.fig_3d, lambda _: self.__plot_3d(), interval=1000)
        #self.animation_2d = animation.FuncAnimation(self.fig_2d, lambda _: self.__plot_2d(), interval=1000)

    """
    Methods for opening the editor windows
    """
    def __find_closest(self, yi, keys):

        i = 0
        mindiff = float('inf')
        while True:
            diff = abs(yi - keys[i])
            if diff < mindiff:
                mindiff = float(diff)
                i += 1
                continue

            return keys[i]

    # TODO: Fix NANs in coordinates
    def project_in_2d(self, array, dictionary, yi=None):

        topdown_coordinates = array[(1,0), :]
        front_coordinates = array[(1,2), :]
        side_coordinates = [[],[]]

        try:
            side_coordinates[0] = list(dictionary[yi]['x'])
            side_coordinates[1] = list(dictionary[yi]['z'])

        except KeyError:
            data = dictionary[self.__find_closest(yi, list(dictionary.keys()))]
            side_coordinates[0] = list(data['x'])
            side_coordinates[1] = list(reversed(data['z']))

        return {
            'topdown': topdown_coordinates,
            'front': front_coordinates,
            'side': np.array(side_coordinates)
        }

    def __plot_3d(self):

        self.plot3d.clear()
        for plot in self.plots2d.values():
            plot.clear()

        arr = self.wing.data_container.get_array()
        dictionary = self.wing.data_container.get_dictionary()

        self.projections = self.project_in_2d(arr, dictionary, yi=self.span_slider.get())  # TODO: Link with slider

        self.plot3d.scatter(arr[0, :], arr[1, :], arr[2, :], c='r', marker='o')
        self.wing.axisEqual3D(self.plot3d)
        self.plot3d.set_xlabel('X [m]')
        self.plot3d.set_ylabel('Y [m]')
        self.plot3d.set_zlabel('Z [m]')

    def __plot_2d(self):

        self.display.config(text=str(round(self.span_slider.get(), 4)))
        self.plots2d['topdown'].plot(
            self.projections['topdown'][0, :],
            self.projections['topdown'][1, :],
            'ro'
        )
        self.plots2d['front'].plot(
            self.projections['front'][0, :],
            self.projections['front'][1, :],
            'ro'
        )
        self.plots2d['side'].plot(
            self.projections['side'][0, :],
            self.projections['side'][1, :],
            'ro'
        )

        for key, plot in self.plots2d.items():

            if key != 'side':
                plot.set_xlim(0, self.wing.get_span())
            else:
                plot.set_xlim(np.min(self.projections[key][0, :]), np.max(self.projections[key][0, :]))

            minmax = (np.min(self.projections[key][1,:]), np.max(self.projections[key][1,:]))
            print(minmax)
            plot.set_ylim(min(minmax), max(minmax))

    def __plot(self):

        self.__plot_3d()
        #self.__plot_2d()


if __name__ == "__main__":

    app = WingEditor()
    app.mainloop()