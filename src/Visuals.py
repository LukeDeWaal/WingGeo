import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import ttk


LARGE_FONT= ("Verdana", 12)


class WingEditor(tk.Tk):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        tk.Tk.wm_title(self, "WingGeo Editor")

        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.pages = args


    def refresh_frames(self):

        for F in self.pages:
            frame = F(self.container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class Page(tk.Frame):

    def __init__(self, parent, controller, name, *args):

        self.controller = controller
        self.name = name
        self.neighbours = args
        self.buttons = []

        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text=self.name, font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        for idx, bt in enumerate(self.neighbours):
            self.buttons.append(ttk.Button(self, text=str(bt),
                                           command=lambda: self.controller.show_frame(bt)))
            self.buttons[idx].pack()


class StartPage(Page):

    def __init__(self, parent, controller, name, *args):

        super().__init__(self, parent, controller, name, *args)

        label = tk.Label(self, text="Start Page", font=LARGE_FONT)
        label.pack(pady=10, padx=10)






class GraphingPage(Page):

    def __init__(self, parent, controller):
