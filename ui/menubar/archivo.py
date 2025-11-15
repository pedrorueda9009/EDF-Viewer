import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ui.edf_viewer_frame import EDFViewerFrame
from ui.mat_viewer_frame import MatViewerFrame
import os
from core.reader import read_mat_safely
from core.summarizer import arr_summary
import numpy as np

class MenuArchivo:
    def __init__(self, mainwindow, root, menubar,notebook):
        """
        root: ventana Tk
        mainwindow: instancia de MainWindow (para poder llamar a open_mat, etc)
        """
        self.root = root
        self.mainwindow = mainwindow
        self.menubar = menubar
        self.notebook = notebook
        self._build_menu()


    def _build_menu(self):

        # Menú Archivo
        archivo_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Archivo", menu=archivo_menu)

        # Opciones
        archivo_menu.add_command(label="Abrir archivo .mat",command=self.open_mat)
        archivo_menu.add_command(label="Abrir archivo .edf",command=self.open_edf)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)

    def open_edf(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo EDF",
            filetypes=[("Archivos EDF", "*.edf"), ("Todos", "*.*")]
        )
        if not path:
            return
        
        # Crear una nueva pestaña en el notebook
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=os.path.basename(path))

        # Insertar el visor dentro de la pestaña
        viewer = EDFViewerFrame(tab, path)
        viewer.pack(fill="both", expand=True)

        # Activar la nueva pestaña
        self.notebook.select(tab)

        # EDFViewerWindow(self.root, path)

    def open_mat(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo .mat",
            filetypes=[("Archivos MATLAB", "*.mat"), ("Todos", "*.*")]
        )
        if not path:
            return
 
        # Crear una nueva pestaña en el notebook
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=os.path.basename(path))

        # Insertar el visor dentro de la pestaña
        viewer = MatViewerFrame(tab, path)
        viewer.pack(fill="both", expand=True)

        # Activar la nueva pestaña
        self.notebook.select(tab)


    # def load_mat(self, path):
    #     data = read_mat_safely(path)
    #     if data is None:
    #         return
    #     self.data = {k: v for k, v in data.items() if not k.startswith("__")}
    #     self.populate_tree()
    #     messagebox.showinfo("Archivo cargado", f"Archivo {os.path.basename(path)} cargado correctamente.\nVariables: {len(self.data)}")

    # def populate_tree(self):
    #     for i in self.tree.get_children():
    #         self.tree.delete(i)

    #     for k, v in self.data.items():
    #         tipo = type(v).__name__
    #         if isinstance(v, np.ndarray):
    #             shape = str(v.shape)
    #         else:
    #             shape = "-"
    #         resumen = arr_summary(v)
    #         self.tree.insert("", "end", values=(k, tipo, shape, resumen))