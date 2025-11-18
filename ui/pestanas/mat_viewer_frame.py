import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from scipy.io import loadmat, savemat
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
from ui.menu_sobre_pestanas.menu_sobre_pestanas import MenuSobrePestanas


class MatViewerFrame(ttk.Frame):
    def __init__(self, master, path):
        super().__init__(master)

        try:
            data = loadmat(path)
            # quitar metadatos de MATLAB (__header__, __version__, __globals__)
            self.data = {k: v for k, v in data.items() if not k.startswith("__")}
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo .mat:\n{e}")
            self.destroy()
            return

        # Estado interno
        self.current_var = None
        self.current_data = None
        self.selected_vector = None

        # --- Layout principal ---
        left = ttk.Frame(self, width=400)
        left.pack(side="left", fill="y", padx=6, pady=6)
        left.pack_propagate(False)

        right = ttk.Frame(self)
        right.pack(side="right", fill="both", expand=True, padx=6, pady=6)
        left.pack_propagate(False)


        self.sub_notebook = ttk.Notebook(right)
        self.sub_notebook.pack(fill="both", expand=True)

        # Crear una sub-pestaña inicial vacía
        initial_tab = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(initial_tab, text="Principal")

        # Guardamos la referencia para poder crear nuevas sub-pestañas más adelante
        self.current_subtab = initial_tab

        # --- Panel izquierdo: lista de variables ---
        info_frame = ttk.Frame(left)
        info_frame.pack(fill="x", pady=(0, 6))
        
        ttk.Label(info_frame, text=f"Archivo: {os.path.basename(path)}",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=6)

        ##############################################################################################
        ttk.Label(left, text="Variables:").pack(anchor="w")

        cols = ("Variable", "Forma", "Tipo")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="w", width=100)

        for k, v in self.data.items():
            try:
                shape = str(np.shape(v))
                tipo = type(v).__name__
            except Exception:
                shape, tipo = "-", "-"
            self.tree.insert("", "end", values=(k, shape, tipo))
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_variable_select)

        #################################################################################### 
        # --- Nuevo panel para contenido textual en el lado izquierdo ---
        self.left_text_frame_container = ttk.Frame(left)
        self.left_text_frame_container.pack(fill="both", expand=False, pady=6)
        ####################################################################################


        # --- Panel derecho: controles y figura ---
        self.controls_frame = ttk.Frame(self.current_subtab)
        self.controls_frame.pack(fill="x", pady=(0, 6))

        # Entradas de título y etiquetas
        title_frame = ttk.Frame(self.controls_frame)
        title_frame.pack(fill="x", pady=4)
        ttk.Label(title_frame, text="Título:").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(title_frame, width=40)
        self.title_entry.grid(row=0, column=1, padx=6, sticky="w")

        ttk.Label(title_frame, text="X label:").grid(row=1, column=0, sticky="w")
        self.xlabel_entry = ttk.Entry(title_frame, width=20)
        self.xlabel_entry.grid(row=1, column=1, padx=6, sticky="w")

        ttk.Label(title_frame, text="Y label:").grid(row=1, column=2, sticky="w", padx=(12, 0))
        self.ylabel_entry = ttk.Entry(title_frame, width=20)
        self.ylabel_entry.grid(row=1, column=3, padx=6, sticky="w")

        apply_btn = ttk.Button(title_frame, text="Aplicar cambios", command=self.update_plot_labels)
        apply_btn.grid(row=0, column=3, padx=6, sticky="e")

        # Botón guardar
        save_btn = ttk.Button(self.controls_frame, text="Guardar .mat (selección)", command=self.save_selection_to_mat)
        save_btn.pack(anchor="e", padx=6, pady=(4, 0))

        # --- Frame de figura ---
        fig_frame = ttk.Frame(self.current_subtab)
        fig_frame.pack(fill="both", expand=True)

        self.fig = plt.Figure(figsize=(8, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=fig_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, fig_frame)
        toolbar.update()

        # creo el menu de cierre de pestaña sobre las subpestañas
        MenuSobrePestanas(self, self.winfo_toplevel(), self.sub_notebook)


    # -------------------------------------------------------------------------
    def on_variable_select(self, event):
        sel = self.tree.selection()

        if not sel:
            return
        
        varname = self.tree.item(sel[0], "values")[0]
        value = self.data[varname]
        self.current_var = varname
        self.current_data = value

        # limpiar controles previos dinámicos (si los hubiera)
        for widget in self.controls_frame.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.destroy()

        if isinstance(value, np.ndarray):

            ndim = value.ndim
            # Mostrar SIEMPRE la matriz/vector en el panel de texto
            self.show_text_content(varname, value)

            # Y además graficar según su dimensión
            if ndim == 1:
                self.plot_vector(value, varname)
            elif ndim == 2:
                self.setup_matrix_selector(value, varname)
            else:
                messagebox.showinfo("No soportado",
                                    f"La variable '{varname}' tiene {ndim} dimensiones.\n"
                                    "Solo se pueden graficar 1D o 2D.")
        else:
            # Solo texto
            self.show_text_content(varname, value)



    # -------------------------------------------------------------------------
    def setup_matrix_selector(self, mat, varname):
        """Crea los controles dinámicos para seleccionar fila o columna."""
        nrows, ncols = mat.shape
        selector_box = ttk.LabelFrame(self.controls_frame, text=f"{varname} — forma {mat.shape}")
        selector_box.pack(fill="x", padx=2, pady=4)

        ttk.Label(selector_box, text="Modo:").grid(row=0, column=0, padx=6, pady=4)
        mode_var = tk.StringVar(value="fila")

        row_btn = ttk.Radiobutton(selector_box, text="Fila", variable=mode_var, value="fila")
        col_btn = ttk.Radiobutton(selector_box, text="Columna", variable=mode_var, value="columna")
        row_btn.grid(row=0, column=1, padx=4)
        col_btn.grid(row=0, column=2, padx=4)

        ttk.Label(selector_box, text="Índice:").grid(row=0, column=3, padx=6)
        index_var = tk.IntVar(value=0)
        index_spin = ttk.Spinbox(selector_box, from_=0, to=nrows - 1, width=6, textvariable=index_var)
        index_spin.grid(row=0, column=4, padx=4)

        def update_spin_range():
            if mode_var.get() == "fila":
                index_spin.config(from_=0, to=nrows - 1)
            else:
                index_spin.config(from_=0, to=ncols - 1)
        mode_var.trace_add("write", lambda *args: update_spin_range())

        def plot_selection():
            idx = index_var.get()
            if mode_var.get() == "fila":
                if idx >= nrows:
                    messagebox.showinfo("Índice inválido", f"Fila {idx} fuera de rango (máx {nrows-1}).")
                    return
                vec = mat[idx, :]
                label = f"{varname}[fila {idx}]"
            else:
                if idx >= ncols:
                    messagebox.showinfo("Índice inválido", f"Columna {idx} fuera de rango (máx {ncols-1}).")
                    return
                vec = mat[:, idx]
                label = f"{varname}[columna {idx}]"

            self.selected_vector = vec
            self.plot_vector(vec, label)

        ttk.Button(selector_box, text="Graficar selección", command=plot_selection).grid(row=0, column=5, padx=8)


    # -------------------------------------------------------------------------
    def plot_vector(self, vec, label):
        """Grafica un vector 1D."""
        try:
            y = np.ravel(vec).astype(float)
        except Exception:
            messagebox.showinfo("Error", f"No se pudo convertir '{label}' a vector numérico.")
            return

        x = np.arange(len(y))
        self.ax.clear()
        self.ax.plot(x, y, linewidth=0.8)
        self.ax.set_title(self.title_entry.get() or label)
        self.ax.set_xlabel(self.xlabel_entry.get() or "Índice")
        self.ax.set_ylabel(self.ylabel_entry.get() or "Valor")
        self.ax.grid(True)
        self.canvas.draw()

        self.selected_vector = y

    def show_text_content(self, varname, value):
        """Muestra arrays como tablas con scroll, o texto si no son arrays."""

        # Eliminar contenido previo
        existing = getattr(self, "left_text_frame", None)
        if existing:
            existing.destroy()

        # Nuevo contenedor
        self.left_text_frame = ttk.LabelFrame(
            self.left_text_frame_container,
            text=f"Contenido de '{varname}'"
        )
        self.left_text_frame.pack(fill="both", expand=True, pady=1)

        # --------------------------------------------
        # 1) Caso: es un numpy array → tabla
        # --------------------------------------------
        if isinstance(value, np.ndarray):

            arr = value

            # Convertimos a dataframe según el número de dimensiones
            if arr.ndim == 1:
                df = pd.DataFrame({"Valor": arr})
            elif arr.ndim == 2:
                df = pd.DataFrame(arr)
            else:
                self._show_text_fallback(value)
                return

            # Limitar columnas si es gigante (opcional)
            max_cols = 100
            if df.shape[1] > max_cols:
                df = df.iloc[:, :max_cols]

            # Crear Treeview con scroll funcional
            frame = ttk.Frame(self.left_text_frame)
            frame.pack(fill="both", expand=True)

            tree = ttk.Treeview(frame, columns=list(df.columns), show="headings")

            # Configurar encabezados y columnas
            for c in df.columns:
                tree.heading(c, text=str(c))
                tree.column(c, width=80, anchor="center")

            # Insertar filas
            for _, row in df.iterrows():
                tree.insert("", "end", values=list(row))

            # Scrollbars
            vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)

            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            # Layout
            tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")

            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

            return

        # --------------------------------------------
        # 2) Caso: NO es array → texto formateado
        # --------------------------------------------
        self._show_text_fallback(value)

    def _show_text_fallback(self, value):
        """Formateo textual para no-arrays."""
        import pprint
        pp = pprint.PrettyPrinter(indent=2, width=80)

        text_widget = tk.Text(
            self.left_text_frame,
            wrap="word",
            height=12,
            background="#fafafa",
            font=("Consolas", 10)
        )
        text_widget.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            self.left_text_frame,
            orient="vertical",
            command=text_widget.yview
        )
        scrollbar.pack(side="right", fill="y")
        text_widget.configure(yscrollcommand=scrollbar.set)

        # elegimos el formato
        if hasattr(value, "__dict__"):
            content = pp.pformat(value.__dict__)
        else:
            content = pp.pformat(value)

        text_widget.insert("1.0", content)
        text_widget.config(state="disabled")

    # -------------------------------------------------------------------------
    def update_plot_labels(self):
        """Actualiza título y etiquetas sin replotear."""
        self.ax.set_title(self.title_entry.get() or self.ax.get_title())
        self.ax.set_xlabel(self.xlabel_entry.get() or "Índice")
        self.ax.set_ylabel(self.ylabel_entry.get() or "Valor")
        self.canvas.draw()


    # -------------------------------------------------------------------------
    def save_selection_to_mat(self):
        """Guarda la señal actualmente graficada."""
        'self.selected_vecor es un array de valores.'
        if self.selected_vector is None:
            messagebox.showinfo("Atención", "Primero graficar una variable o selección.")
            return

        out = filedialog.asksaveasfilename(defaultextension=".mat", filetypes=[("MAT-files", "*.mat")])
        if not out:
            return

        tosave = {
            "variable": np.array(self.current_var, dtype=object),
            "signal": np.array(self.selected_vector),
        }
        try:
            savemat(out, tosave)
            messagebox.showinfo("Guardado", f"Guardado correctamente en:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo .mat:\n{e}")


    def get_current_signal(self):
        if self.selected_vector is None:
            return None
        return self.selected_vector