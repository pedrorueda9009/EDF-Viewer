import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
import mne
from scipy.io import savemat
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from ui.menu_sobre_pestanas.menu_sobre_pestanas import MenuSobrePestanas


# ---------------------------
# Ventana para archivos EDF
# ---------------------------
class EDFViewerFrame(ttk.Frame):
    def __init__(self, master, path):
        super().__init__(master)

        try:
            try:
                # Intento estándar (UTF-8)
                self.raw = mne.io.read_raw_edf(
                    path, 
                    preload=True, 
                    verbose=False
                )

            except UnicodeDecodeError:
                # Fallback si la cabecera está en Latin-1 u otra codificación rara
                try:
                    self.raw = mne.io.read_raw_edf(
                        path,
                        preload=True,
                        verbose=False,
                        encoding="latin1"
                    )
                except Exception as e_inner:
                    messagebox.showerror(
                        "Error",
                        f"No se pudo abrir el archivo EDF (problema de codificación).\n\n{e_inner}"
                    )
                    self.destroy()
                    return

            except ValueError as e:
                # Error clásico: EDF corrupto, truncado o mal formado
                messagebox.showerror(
                    "Error",
                    f"El archivo EDF parece estar dañado o incompleto.\n\n{e}"
                )
                self.destroy()
                return

            except OSError as e:
                # Permisos, archivo inexistente, path inválido
                messagebox.showerror(
                    "Error",
                    f"No se pudo acceder al archivo EDF.\n\n{e}"
                )
                self.destroy()
                return

        except Exception as e:
            # Cualquier cosa inesperada (muy raro)
            messagebox.showerror(
                "Error",
                f"Ocurrió un error inesperado al cargar el archivo EDF:\n\n{e}"
            )
            self.destroy()
            return


        # señales y metadatos
        self.data = self.raw.get_data()            # shape: (n_channels, n_samples)
        self.info = self.raw.info
        self.ch_names = self.info["ch_names"]
        self.fs = float(self.info["sfreq"])

        # anotaciones: pueden no existir
        self.annotations = []
        try:
            ann = self.raw.annotations
            # ann tiene onset, duration, description
            for onset, duration, desc in zip(ann.onset, ann.duration, ann.description):
                self.annotations.append({'onset': float(onset), 'duration': float(duration), 'desc': str(desc)})
        except Exception:
            self.annotations = []

        # estado de UI
        self.current_channel_idx = None
        self.current_line_objs = []   # referencias a líneas verticales en el plot
        self.marker_vars = []         # variables tk.IntVar para checkboxes

        # --- Layout: izquierda = lista canales, derecha = gráfica + controles ---
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=4, pady=4)
        right = ttk.Frame(self)
        right.pack(side="right", fill="both", expand=True, padx=4, pady=4)

        # --- Frame derecho: sub-notebook ---
        self.sub_notebook = ttk.Notebook(right)
        self.sub_notebook.pack(fill="both", expand=True, padx=1, pady=1)

        # Crear una sub-pestaña inicial vacía
        initial_tab = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(initial_tab, text="Principal")

        # Guardamos la referencia para poder crear nuevas sub-pestañas más adelante
        self.current_subtab = initial_tab

        # creo el menu de cierre de pestaña sobre las subpestañas
        MenuSobrePestanas(self, self.winfo_toplevel(), self.sub_notebook)


        # --- Left: info general y lista canales ---
        info_frame = ttk.Frame(left)
        info_frame.pack(fill="x", pady=(0,6))
        ttk.Label(info_frame, text=f"Archivo: {os.path.basename(path)}", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(info_frame, text=f"Canales: {len(self.ch_names)}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Fs: {self.fs} Hz").pack(anchor="w")
        ttk.Label(info_frame, text=f"Duración: {self.data.shape[1] / self.fs:.2f} s").pack(anchor="w")

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=6)

        ttk.Label(left, text="Canales:").pack(anchor="w")
        cols = ("Canal", "Forma")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="w", width=160)
        for idx, ch in enumerate(self.ch_names):
            self.tree.insert("", "end", values=(ch, str(self.data[idx].shape)))
        self.tree.pack(fill="y", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.on_channel_select())

        # --- Right: top controls (annotations checkboxes + title/axis inputs) ---
        # controls = ttk.Frame(right)
        controls = ttk.Frame(self.current_subtab)
        controls.pack(fill="x", pady=(0,6))
        
        # anotaciones (scrollable + en columnas)
        ann_box = ttk.LabelFrame(controls, text="Marcadores (anotaciones) — seleccionar para mostrar verticales")
        ann_box.pack(fill="x", padx=2, pady=2)

        # Frame para el canvas + scrollbar
        scroll_container = ttk.Frame(ann_box)
        scroll_container.pack(fill="x", expand=True)

        # Canvas y scrollbar vertical
        canvas = tk.Canvas(scroll_container, height=80)  # ajustable
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interno donde van los checkboxes
        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def _on_frame_configure(event):
            """Actualizar región scrollable"""
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", _on_frame_configure)

        # Crear checkboxes dentro del inner_frame en columnas
        self.marker_vars = []
        max_show = len(self.annotations)

        if max_show == 0:
            ttk.Label(inner_frame, text="No hay anotaciones en este EDF.").grid(row=0, column=0, padx=6, pady=4)
        else:
            num_cols = 3   # <--- Ajustá aquí cuántas columnas querés

            for i in range(max_show):
                var = tk.IntVar(value=0)
                self.marker_vars.append(var)

                desc = self.annotations[i]['desc']
                onset = self.annotations[i]['onset']

                cb = ttk.Checkbutton(
                    inner_frame,
                    text=f"{desc} @ {onset:.2f}s",
                    variable=var,
                    command=self.update_markers_on_plot
                )

                # distribuir en filas/columnas
                row = i // num_cols
                col = i % num_cols

                cb.grid(row=row, column=col, sticky="w", padx=6, pady=2)

            # permitir que las columnas crezcan
            for c in range(num_cols):
                inner_frame.grid_columnconfigure(c, weight=1)


        # título y ejes
        title_frame = ttk.Frame(controls)
        title_frame.pack(fill="x", pady=4)

        ttk.Label(title_frame, text="Título:").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(title_frame, width=40)
        self.title_entry.grid(row=0, column=1, padx=6, sticky="w")

        ttk.Label(title_frame, text="X label:").grid(row=1, column=0, sticky="w")
        self.xlabel_entry = ttk.Entry(title_frame, width=20)
        self.xlabel_entry.grid(row=1, column=1, padx=6, sticky="w")

        ttk.Label(title_frame, text="Y label:").grid(row=1, column=2, sticky="w", padx=(12,0))
        self.ylabel_entry = ttk.Entry(title_frame, width=20)
        self.ylabel_entry.grid(row=1, column=3, padx=6, sticky="w")

        apply_btn = ttk.Button(title_frame, text="Aplicar cambios", command=self.update_plot_labels)
        apply_btn.grid(row=0, column=3, padx=6, sticky="e")

        # guardar selección a .mat
        save_btn = ttk.Button(controls, text="Guardar .mat (selección)", command=self.save_selection_to_mat)
        save_btn.pack(anchor="e", padx=6, pady=(4,0))


        # --- Right: figura (matplotlib) ---
        # fig_frame = ttk.Frame(right)
        fig_frame = ttk.Frame(self.current_subtab)
        fig_frame.pack(fill="both", expand=True)

        self.fig = plt.Figure(figsize=(8,4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = None
        # use FigureCanvasTkAgg only when drawing to avoid import hassle at top-level

        self.canvas = FigureCanvasTkAgg(self.fig, master=fig_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, fig_frame)
        toolbar.update()


    def on_channel_select(self):
        """Llamar al hacer doble clic en la lista de canales."""
        sel = self.tree.selection()
        if not sel:
            return
        canal = self.tree.item(sel[0], "values")[0]
        idx = self.ch_names.index(canal)
        self.current_channel_idx = idx
        self.plot_channel(idx)

    def plot_channel(self, idx):
        """Grafica la señal completa del canal idx y aplica marcadores/etiquetas actuales."""
        y = self.data[idx, :]
        x = np.arange(len(y)) / self.fs

        self.ax.clear()
        self.ax.plot(x, y, linewidth=0.6, label=self.ch_names[idx])
        self.ax.set_title(self.title_entry.get() if self.title_entry.get() else f"Canal: {self.ch_names[idx]}")
        self.ax.set_xlabel(self.xlabel_entry.get() if self.xlabel_entry.get() else "Tiempo [s]")
        self.ax.set_ylabel(self.ylabel_entry.get() if self.ylabel_entry.get() else "Amplitud")
        self.ax.grid(True)

        # dibujar marcadores verticales seleccionados
        self.current_line_objs = []
        for i, var in enumerate(self.marker_vars):
            if var.get() == 1 and i < len(self.annotations):
                onset = self.annotations[i]['onset']
                line = self.ax.axvline(onset, color='red', linestyle='--', linewidth=1.2)
                self.current_line_objs.append(line)

        self.ax.legend()
        self.canvas.draw()

    def update_markers_on_plot(self):
        """Actualizar solo las líneas verticales sin replotear toda la señal (si canal ya está graficado)."""
        if self.current_channel_idx is None:
            return
        # quitar líneas previas
        for ln in getattr(self, "current_line_objs", []):
            try:
                ln.remove()
            except Exception:
                pass
        self.current_line_objs = []
        # agregar las nuevas
        for i, var in enumerate(self.marker_vars):
            if var.get() == 1 and i < len(self.annotations):
                onset = self.annotations[i]['onset']
                line = self.ax.axvline(onset, color='red', linestyle='--', linewidth=1.2)
                self.current_line_objs.append(line)
        self.canvas.draw()

    def update_plot_labels(self):
        """Leer entradas y actualizar título/labels en el plot actual."""
        if self.current_channel_idx is None:
            messagebox.showinfo("Atención", "Primero grafique un canal.")
            return
        self.ax.set_title(self.title_entry.get() if self.title_entry.get() else f"Canal: {self.ch_names[self.current_channel_idx]}")
        self.ax.set_xlabel(self.xlabel_entry.get() if self.xlabel_entry.get() else "Tiempo [s]")
        self.ax.set_ylabel(self.ylabel_entry.get() if self.ylabel_entry.get() else "Amplitud")
        self.canvas.draw()

    def save_selection_to_mat(self):
        """Guarda en .mat: señal completa del canal seleccionado, anotaciones seleccionadas, fs y nombre canal."""
        'self.current_channel_idx es un indice del canal que elijo'
        if self.current_channel_idx is None:
            messagebox.showinfo("Atención", "Primero grafique y seleccione un canal.")
            return
        
        idx = self.current_channel_idx
        channel_name = self.ch_names[idx]
        signal = self.data[idx, :]

        # recolectar marcadores seleccionados
        markers = []
        for i, var in enumerate(self.marker_vars):
            if var.get() == 1 and i < len(self.annotations):
                markers.append(self.annotations[i])

        out = filedialog.asksaveasfilename(defaultextension=".mat", filetypes=[("MAT-files","*.mat")])
        if not out:
            return
        tosave = {
            'channel_name': np.array(channel_name, dtype=object),
            'fs': float(self.fs),
            'signal': signal,
            'markers': np.array(markers, dtype=object),
        }
        try:
            savemat(out, tosave)
            messagebox.showinfo("Guardado", f"Guardado correctamente en:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar .mat:\n{e}")

    def add_stat_subtab(self, stat_name):
        """Crea una nueva sub-pestaña en el sub-notebook para una estadística."""
        tab = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(tab, text=stat_name)
        self.sub_notebook.select(tab)

        # Panel de controles
        tab.controls_frame = ttk.Frame(tab)
        tab.controls_frame.pack(fill="x", pady=(0, 6))

        # Panel de figura
        tab.fig_frame = ttk.Frame(tab)
        tab.fig_frame.pack(fill="both", expand=True)

        # Crear figura y canvas
        tab.fig = plt.Figure(figsize=(8, 4))
        tab.ax = tab.fig.add_subplot(111)
        tab.canvas = FigureCanvasTkAgg(tab.fig, master=tab.fig_frame)
        tab.canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(tab.canvas, tab.fig_frame)
        toolbar.update()

        return tab

    def get_current_signal(self):
        if self.current_channel_idx is None:
            return None
        idx = self.current_channel_idx
        return self.data[idx, :]
