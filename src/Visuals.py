import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from matplotlib import style
style.use('ggplot')

import numpy as np
import tkinter as tk
from tkinter import ttk

from WingTool import Wing


LARGE_FONT = ("Verdana", 12)


class WingEditor(tk.Tk):

    def __init__(self, *args, **kwargs):

        if 'n' in kwargs.keys():
            self.n = kwargs['n']
            del kwargs['n']

        else:
            self.n = 100

        self.wing = Wing(n_steps=self.n)

        super().__init__(*args, **kwargs)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        tk.Tk.wm_title(self, "WingGeo Editor")

        self.wing = Wing(self.n)

        self.plot_container = tk.Frame(self)
        self.plot_container.grid(row=0, column=0)

        self.editor_container = tk.Frame(self)
        self.editor_container.grid(row=0, column=1)
        self.editor_container.columnconfigure(1, weight=1)
        self.editor_container.rowconfigure(1, weight=1)
        self.editor_container.rowconfigure(2, weight=1)

        # Menu Bar Creation
        self.menubar = tk.Menu(self.master)
        self.config(menu=self.menubar)

        # File Menu
        fileMenu = tk.Menu(self.menubar)
        fileMenu.config(tearoff=False)
        fileMenu.add_command(label="Exit", command=lambda: None)
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
            'Airfoils',
            'Chord',
            'Sweep',
            'Twist',
            'Dihedral',
            'Span Steps',
            'Airfoil Steps'
        ]

        self.parameter_labels = {}
        self.parameter_entries = {}
        self.parameter_variables = {label: tk.StringVar() for label in self.parameter_label_texts}

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

            self.parameter_entries[label] = ttk.Entry(
                                                self.editor_container,
                                                textvariable=self.parameter_variables[label]
                                            )

            self.parameter_variables[label].set(0)
            self.parameter_entries[label].grid(
                row=idx,
                column=1,
                sticky='N',
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
            sticky='N',
            padx=SPACING[0],
            pady=SPACING[1]
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

        self.cosine_box = ttk.Checkbutton(
            self.lower_box,
            text="Cosine Spacing",
            var=self.cosine_var
        )
        self.cosine_box.grid(
            row=0,
            column=1
        )

        for idx in range(len(self.parameter_labels)+1):
            self.editor_container.rowconfigure(idx, weight=1)

    def __extract_inputs(self):

        input_values = {}

        for label, var in self.parameter_variables.items():

            value = var.get()

            if label not in self.parameter_label_texts[-2:]:
                try:
                    value = float(value)

                except (ValueError, TypeError):
                    pass

            else:
                try:
                    value = int(value)

                except (ValueError, TypeError):
                    pass

            input_values[label] = value

        return input_values

    def __plot(self):

        arr = self.wing.data_container.get_array()

        self.plot3d.scatter(arr[0, :], arr[1, :], arr[2, :], c='r', marker='o')
        self.plot3d.set_xlabel('X [m]')
        self.plot3d.set_ylabel('Y [m]')
        self.plot3d.set_zlabel('Z [m]')

        self.wing.axisEqual3D(self.plot3d)

    def __update_plot(self):

        self.plot3d.clear()

        # self.plot3d.plot(x, y, z)
        print("Updating")
        values = self.__extract_inputs()
        print(values)

        self.wing.set_cosine_spacing(self.cosine_var.get())

        self.wing.set_spanwise_steps(values['Span Steps'])
        self.wing.set_airfoil_steps(values['Airfoil Steps'])

        self.wing.set_span(values['Span'])
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