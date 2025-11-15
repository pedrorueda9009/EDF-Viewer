import os
import tkinter as tk
from tkinter import ttk
import numpy as np
# from ui.mat_viewer_frame import MatViewerFrame
# from ui.edf_viewer_frame import EDFViewerFrame
# from core.estadisticas import band_and_pompe

from ui.menubar.archivo import MenuArchivo
from ui.menubar.estadisticas import MenuEstadisticas
from ui.pestanas.menu_sobre_pestanas import MenuSobrePestanas

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("EDF Viewr")
        self.root.geometry("800x800")
        self.data = None
        self.path = None

        menubar = tk.Menu(root)
        root.config(menu=menubar)

        # Área principal: Notebook (pestañas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # Pestaña inicial vacía o con instrucciones
        home = ttk.Frame(self.notebook)
        ttk.Label(home, text="Abra un archivo .mat o .edf desde la barra superior").pack(padx=20, pady=20)
        self.notebook.add(home, text="Inicio")

        # Menú principal
        MenuArchivo(self, root, menubar, self.notebook)
        # Menú Estadísticas
        MenuEstadisticas(self, menubar,self.notebook)
        # Menu sobre pestañas
        MenuSobrePestanas(self, root, self.notebook)
