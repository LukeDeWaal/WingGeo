import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseEvent
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from matplotlib import style
style.use('ggplot')

import numpy as np
import os, math
import tkinter as tk
from tkinter import ttk

from WingTool import Wing
from TkTable import Tk_Table


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
        fileMenu.add_command(label="Save", command=lambda: None)
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

            self.table.insert_row([self.table[(self.table.number_of_rows - 1, 1)], float(self.get_span()), 10],
                                  self.table.number_of_rows)

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
            command=lambda: None
        )
        self.reset_btn.grid(
            row=0,
            column=2,
            sticky='n',
        )

        self.clear_btn = ttk.Button(
            self.btn_frame,
            text='Delete',
            command=lambda: self.table.delete_all_selected_rows() and self.update_plot()
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

        self.table = Tk_Table(
            self.entry_frame,
            ['Start', 'Stop', 'Steps'],
            height=30
        )

        self.table.insert_row([0, self.get_span(), 10])

        self.table.grid(
            row=0,
            column=0,
            sticky='nw'
        )

        self.plotting_frame = tk.Frame(self)
        self.plotting_frame.grid(row=1, column=1, sticky='nw')

        self._figure, self.plot, self._line, self._connectors = None, None, None, None
        self._dragging_point = None
        self._points = {}

        self.xlim = (0, float(self.get_span()))
        self.ylim = (0, 100)

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

    def __update_table_and_plot(self, event):

        if len(self.table.selected_rows) > 0:
            self.table.deselect_all()
            self.table_to_plot()
        else:
            pass

    def get_span(self):
        return self.master.parameter_variables['Span'].get()

    def __apply(self):
        pass

    def __open(self):
        pass

    def __save(self):
        pass

    def __new(self):
        pass

    def table_to_plot(self):

        self._points = {}

        for i in range(self.table.number_of_rows):
            point = (float(self.table[(i, 0)]), int(self.table[(i, 2)]))
            self._add_point(*point)

        self._add_point(float(self.table[(i, 1)]), int(self.table[(i, 2)]))
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
            self.table.insert_row([round(xsort[idx], 3), round(xsort[idx+1], 3), int(ysort[idx])])

        self.table.sort_by(0, False)

    def _init_plot(self):

        self.plot.set_xlim(*self.xlim)
        self.plot.set_ylim(*self.ylim)
        self.plot.grid(which="both")

        self._figure.canvas.mpl_connect('button_press_event', self._on_click)
        self._figure.canvas.mpl_connect('button_release_event', self._on_release)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_motion)

        self._add_point(0, 10)
        self._add_point(float(self.get_span()), 10)
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

        self.wing = Wing()

        super().__init__(*args, **kwargs)
        # self.geometry(ROOT_GEO)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        tk.Tk.wm_title(self, "WingGeo Editor")

        self.wing = Wing()

        self.plot_container = tk.Frame(self)
        self.plot_container.grid(row=0, column=0)

        self.editor_container = tk.Frame(self)
        self.editor_container.grid(row=0, column=1)
        self.editor_container.grid_columnconfigure(1, weight=1)
        self.editor_container.grid_rowconfigure(0, weight=1)
        self.editor_container.grid_rowconfigure(1, weight=1)

        # Menu Bar Creation
        self.menubar = tk.Menu(self.master)
        self.config(menu=self.menubar)

        # File Menu
        fileMenu = tk.Menu(self.menubar)
        fileMenu.config(tearoff=False)
        fileMenu.add_command(label="Exit", command=lambda: quit())
        self.menubar.add_cascade(label="File", menu=fileMenu)

        """
        Plotting Frame
        """
        fig = Figure(figsize=(5, 5), dpi=100)

        canvas = FigureCanvasTkAgg(fig, self.plot_container)
        canvas.draw()

        self.plot3d = fig.add_subplot(111, projection="3d")

        toolbar = NavigationToolbar2Tk(canvas, self.plot_container)
        toolbar.update()

        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


        """
        Editing Frame
        """
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

        self.parameter_labels = {}
        self.parameter_entries = {}
        self.parameter_variables = {label: tk.StringVar() for label in self.parameter_label_texts[:2]}

        SPACING = (5, 20)

        for idx, label in enumerate(self.parameter_label_texts):

            self.parameter_labels[label] = ttk.Label(
                                                self.editor_container,
                                                text=label
                                          )

            self.parameter_labels[label].grid(
                row=idx,
                column=0,
                sticky='N',
                padx=SPACING[0],
                pady=SPACING[1]
            )

            if 0 <= idx <= 1:
                self.parameter_entries[label] = ttk.Entry(
                                                    self.editor_container,
                                                    textvariable=self.parameter_variables[label]
                                                )

                self.parameter_variables[label].set(10)
                self.parameter_entries[label].grid(
                    row=idx,
                    column=1,
                    sticky='N',
                    padx=SPACING[0],
                    pady=SPACING[1]
                )

            else:

                if label == "Span Distr.":
                    command = self.__open_span_editor

                elif label == 'Airfoils':
                    command = self.__open_airfoil_editor

                elif label == 'Chord':
                    command = self.__open_chord_editor

                elif label == 'Sweep':
                    command = self.__open_sweep_editor

                elif label == 'Twist':
                    command = self.__open_twist_editor

                elif label == 'Dihedral':
                    command = self.__open_dihedral_editor

                else:
                    raise ValueError("Unexpected Input")

                self.parameter_entries[label] = ttk.Button(
                    self.editor_container,
                    text="Edit",
                    command=command,
                    state=tk.DISABLED if label != 'Span Distr.' else tk.NORMAL
                )

                self.parameter_entries[label].grid(
                    row=idx,
                    column=1,
                    sticky='NSEW',
                    padx=SPACING[0],
                    pady=SPACING[1]
                )

        self.editor_container.columnconfigure(0, weight=1)
        self.editor_container.columnconfigure(1, weight=1)

        self.lower_box = tk.Frame(self.editor_container)
        self.lower_box.grid(
            row=len(self.parameter_labels),
            column=0,
            columnspan=2,
            sticky='NSEW',
            padx=SPACING[0],
            pady=SPACING[1]
        )

        self.tickbox_frame = tk.Frame(self.lower_box)
        self.tickbox_frame.grid(
            row=0,
            column=1,
            sticky='NSEW'
        )

        self.refresh_button = ttk.Button(
            self.lower_box,
            text="Update",
            command=self.__update_plot
        )
        self.refresh_button.grid(
            row=0,
            column=0
        )
        self.cosine_var = tk.BooleanVar()
        self.cosine_var.set(False)

        self.custom_var = tk.BooleanVar()
        self.custom_var.set(False)

        self.cosine_box = ttk.Checkbutton(
            self.tickbox_frame,
            text="Cosine Spacing",
            var=self.cosine_var
        )
        self.cosine_box.grid(
            row=0,
            column=0,
            sticky='W',
            padx=5
        )

        self.custom_box = ttk.Checkbutton(
            self.tickbox_frame,
            text="Custom Grid",
            var=self.custom_var
        )
        self.custom_box.grid(
            row=1,
            column=0,
            sticky='W',
            padx=5
        )

        for idx in range(len(self.parameter_labels)+1):
            self.editor_container.rowconfigure(idx, weight=1)

        self.parameter_variables['Span'].trace_add(
            "write",
            lambda name, index, mode: self.__entry_box_change()
        )
        self.parameter_variables['Airfoil Steps'].trace_add(
            "write",
            lambda name, index, mode: self.__entry_box_change()
        )

        self.editor_windows = {}


    def __parser(self):
        pass

    def __entry_box_change(self):
        """
        Keeps track of the the span and discretization values
        and blocks further editing if necessary
        """

        if self.parameter_variables['Span'].get() == "" or \
                self.parameter_variables['Airfoil Steps'].get() == "":

            for label in self.parameter_label_texts[2:]:
                self.parameter_entries[label].config(state=tk.DISABLED)

        elif int(self.parameter_variables['Span'].get()) > 0 and \
                int(self.parameter_variables['Airfoil Steps'].get()) > 0:

            self.parameter_entries['Span Distr.'].config(state=tk.NORMAL)
            for label in self.parameter_label_texts[3:]:
                self.parameter_entries[label].config(state=tk.DISABLED)

        else:

            for label in self.parameter_label_texts[3:]:
                self.parameter_entries[label].config(state=tk.DISABLED)

    """
    Methods for opening the editor windows
    """
    def __open_editor(self, name: str):

        if name in self.editor_windows.keys():
            self.editor_windows[name]['window'].update_plot()
            self.editor_windows[name]['window'].deiconify()

        else:
            self.editor_windows[name] = {
                'window': EditorWindow(self, name),
                'state': False
            }
            self.editor_windows[name]['window'].protocol('WM_DELETE_WINDOW',
                                                          self.editor_windows[name]['window'].withdraw)


    def __open_span_editor(self):
        self.__open_editor('Span Distr.')

    def __open_airfoil_editor(self):
        self.__open_editor('Airfoils')

    def __open_chord_editor(self):
        self.__open_editor('Chord')

    def __open_sweep_editor(self):
        self.__open_editor('Sweep')

    def __open_twist_editor(self):
        self.__open_editor('Twist')

    def __open_dihedral_editor(self):
        self.__open_editor('Dihedral')

    def __plot(self):

        arr = self.wing.data_container.get_array()

        self.plot3d.scatter(arr[0, :], arr[1, :], arr[2, :], c='r', marker='o')
        self.wing.axisEqual3D(self.plot3d)
        self.plot3d.set_xlabel('X [m]')
        self.plot3d.set_ylabel('Y [m]')
        self.plot3d.set_zlabel('Z [m]')

    def __update_plot(self):

        self.plot3d.clear()

        # self.plot3d.plot(x, y, z)
        print("Updating")
        values = self.__parser()
        print(values)

        values['Span'] = float(self.parameter_variables['Span'].get())
        values['Span Steps'] = int(self.parameter_variables['Span Steps'].get())
        values['Airfoil Steps'] = int(self.parameter_variables['Airfoil Steps'].get())

        self.wing.set_cosine_spacing(self.cosine_var.get())

        self.wing.set_spanwise_steps(values['Span Steps'])
        self.wing.set_airfoil_steps(values['Airfoil Steps'])

        self.wing.set_airfoil(values['Airfoils'])
        self.wing.set_chord(values['Chord'])
        self.wing.set_sweep(values['Sweep'])
        self.wing.set_twist(values['Twist'])
        self.wing.set_dihedral(values['Dihedral'])

        self.wing.construct()
        self.__plot()


if __name__ == "__main__":

    app = WingEditor()

    app.mainloop()