import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from matplotlib import style
style.use('ggplot')

import numpy as np
import os
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
        # self.geometry(EDITOR_GEO)  # TODO: Make modular with main window

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
            text='New Section',
            command=lambda: None
        )
        self.apply_btn.grid(
            row=0,
            column=0,
            sticky='n',
        )

        self.reset_btn = ttk.Button(
            self.btn_frame,
            text='Reset',
            command=lambda: None
        )
        self.reset_btn.grid(
            row=0,
            column=1,
            sticky='n',
        )

        self.clear_btn = ttk.Button(
            self.btn_frame,
            text='Delete',
            command=lambda: None
        )
        self.clear_btn.grid(
            row=0,
            column=2,
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

        fig = Figure(figsize=(5, 5), dpi=100)

        canvas = FigureCanvasTkAgg(fig, self.plotting_frame)
        canvas.draw()

        self.plot = fig.subplots(1, 1)


        toolbar = NavigationToolbar2Tk(canvas, self.plotting_frame)
        toolbar.update()

        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.plot.set_xlim(0, float(self.get_span()))

    def get_span(self):
        return self.master.parameter_variables['Span'].get()

    def update_plot(self):
        pass



    def __retrieve_input(self):
        pass

    def __apply(self):
        pass

    def __open(self):
        pass

    def __save(self):
        pass

    def __new(self):
        pass


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
                print(label)

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