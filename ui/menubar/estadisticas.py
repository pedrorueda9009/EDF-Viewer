
import tkinter as tk
from tkinter import ttk, messagebox
from ui.mat_viewer_frame import MatViewerFrame
from ui.edf_viewer_frame import EDFViewerFrame
from core.estadisticas import band_and_pompe
import numpy as np

class MenuEstadisticas:
    def __init__(self,mainwindow,menubar,notebook):
        self.mainwindow=mainwindow
        self.menubar = menubar
        self.notebook = notebook
        self._build_menu()
        
    def _build_menu(self):
        stats_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Estadísticas", menu=stats_menu)
        stats_menu.add_command(label="Bandt & Pompe", command=lambda: self.open_stat_tab("Bandt & Pompe"))

    def open_stat_tab(self, stat_name):
        """Abre una sub-pestaña de estadística en la pestaña actual."""
        current_tab = self.notebook.nametowidget(self.notebook.select())
        
        # Cada viewer (EDF o MAT) debe tener método add_stat_subtab
        if hasattr(current_tab, "winfo_children") and len(current_tab.winfo_children()) > 0:
            # viewer_frame = current_tab.winfo_children()[0]
            viewer_frame = self.get_current_viewer()
            if viewer_frame is None:
                messagebox.showerror("Error", "No se detectó un visor de datos en esta pestaña.")
                return
            if hasattr(viewer_frame, "add_stat_subtab"):
                subtab = viewer_frame.add_stat_subtab(stat_name)
                
                # Agregar controles específicos para la estadística
                if stat_name == "Bandt & Pompe":
                    self.setup_bandt_pompe_controls(viewer_frame, subtab)
                    
                    
            else:
                messagebox.showinfo("Error", "La pestaña actual no soporta estadísticas.")
        else:
            messagebox.showinfo("Error", "No hay contenido en la pestaña seleccionada.")

    def get_current_viewer(self):
        """Devuelve el frame viewer (EDF o MAT) de la pestaña actual."""
        current_tab = self.notebook.nametowidget(self.notebook.select())

        for child in current_tab.winfo_children():
            if isinstance(child, (EDFViewerFrame, MatViewerFrame)):
                return child

        return None

    def run_bandt_pompe(self, tab, tau, dim, step, win):
        # Obtener el viewer activo en la pestaña actual
        # edf_mat_frame = self.get_current_viewer()
        viewer = self.get_current_viewer()

        if viewer is None:
            messagebox.showerror("Error", "No se encontró un visor EDF o MAT en esta pestaña.")
            return

        signal = viewer.get_current_signal()
        
        if signal is None:
            messagebox.showinfo("Atención", "No hay señal seleccionada.")
            return
        
        # # Verificar que el usuario seleccionó y graficó un canal
        # if edf_mat_frame.current_channel_idx is None:
        #     messagebox.showinfo("Atención", "Primero selecciona y grafica un canal.")
        #     return

        # # Datos del canal seleccionado
        # idx = edf_mat_frame.current_channel_idx
        # signal = edf_mat_frame.data[idx, :]
        signal = np.asarray(signal, dtype=float)
        
        # Calcular Bandt & Pompe
        try:
            freqs, Hnorm, times = band_and_pompe(
                signal,
                dim,     # dimensión embedding
                tau,     # retardo
                win,     # tamaño ventana
                step,    # paso
                graf=False,
                beat_times=None
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        # Graficar
        tab.ax.clear()
        tab.ax.plot(Hnorm, linewidth=1)
        tab.ax.set_title("Entropía Bandt & Pompe (normalizada)")
        tab.ax.set_xlabel("Ventana")
        tab.ax.set_ylabel("H_norm")
        tab.ax.grid(True)
        tab.canvas.draw()


    def setup_bandt_pompe_controls(self, viewer, subtab):
        """Agrega controles específicos de Bandt & Pompe en la sub-pestaña."""
        controls = ttk.LabelFrame(subtab.controls_frame, text="Parámetros Bandt & Pompe")
        controls.pack(fill="x", padx=2, pady=4)

        # Ejemplo de controles: retardo, dimensión embedding, paso, ventana
        ttk.Label(controls, text="Retardo:").grid(row=0, column=0, padx=4, pady=2)
        tau_var = tk.IntVar(value=1)
        ttk.Spinbox(controls, from_=1, to=20, width=5, textvariable=tau_var).grid(row=0, column=1, padx=4)

        ttk.Label(controls, text="Dimensión embedding:").grid(row=0, column=2, padx=4, pady=2)
        dim_var = tk.IntVar(value=3)
        ttk.Spinbox(controls, from_=2, to=10, width=5, textvariable=dim_var).grid(row=0, column=3, padx=4)

        ttk.Label(controls, text="Paso:").grid(row=1, column=0, padx=4, pady=2)
        step_var = tk.IntVar(value=1)
        ttk.Spinbox(controls, from_=1, to=10, width=5, textvariable=step_var).grid(row=1, column=1, padx=4)

        ttk.Label(controls, text="Ventana:").grid(row=1, column=2, padx=4, pady=2)
        win_var = tk.IntVar(value=100)
        ttk.Spinbox(controls, from_=10, to=1000, width=6, textvariable=win_var).grid(row=1, column=3, padx=4)

        ttk.Button(controls, text="Calcular",
                            command=lambda: self.run_bandt_pompe(
                                subtab,
                                tau_var.get(),
                                dim_var.get(),
                                step_var.get(),
                                win_var.get()
                            )).grid(row=2, column=0, columnspan=4, pady=6)

