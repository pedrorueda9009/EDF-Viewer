import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


"""Crea una nueva sub-pestaña en el sub-notebook para una estadística."""
class AddStatSubtab(ttk.Frame):

    def __init__(self, viewer, stat_name):

        super().__init__(viewer)
        self.stat_name = stat_name
        self.viewer = viewer
        self.controls_frame = None
        self.fig_frame = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self._build_stat_subtab()

        # 3. Añadir esta instancia (self) al notebook
        self.viewer.sub_notebook.add(self, text=self.stat_name)
        self.viewer.sub_notebook.select(self)

    def _build_stat_subtab(self):
        
        # Panel de controles
        self.controls_frame = ttk.Frame(self)
        self.controls_frame.pack(fill="x", pady=(0, 6))

        # Panel de figura
        self.fig_frame = ttk.Frame(self)
        self.fig_frame.pack(fill="both", expand=True)

        # Crear figura y canvas
        self.fig = plt.Figure(figsize=(8, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.fig_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, self.fig_frame)
        toolbar.update()
