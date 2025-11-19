
import tkinter as tk
from tkinter import ttk, messagebox, filedialog 
from ui.pestanas.mat_viewer_frame import MatViewerFrame
from ui.pestanas.edf_viewer_frame import EDFViewerFrame
from core.estadisticas import band_and_pompe, calculate_ibi, calculate_tau_d_heatmap
import numpy as np
from ui.estadisticas.stat_subtab import AddStatSubtab
from scipy.io import savemat # Requerir scipy.io para guardar .mat


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
        stats_menu.add_command(label="IBI", command=lambda: self.open_stat_tab("IBI"))
        stats_menu.add_command(label = "tau(d) HeatMap", command = lambda: self.open_stat_tab("tau_d_heatmap"))

    def open_stat_tab(self, stat_name):
        """Abre una sub-pestaña de estadística en la pestaña actual."""
        current_tab = self.notebook.nametowidget(self.notebook.select())
        
        # Cada viewer (EDF o MAT) debe tener método add_stat_subtab
        if hasattr(current_tab, "winfo_children") and len(current_tab.winfo_children()) > 0:
            
            viewer_frame = self.get_current_viewer()

            if viewer_frame is None:
                messagebox.showerror("Error", "No se detectó un visor de datos en esta pestaña.")
                return


            # subtab = viewer_frame.add_stat_subtab(stat_name)
            subtab = AddStatSubtab(viewer_frame, stat_name)
            
            # Agregar controles específicos para la estadística
            if stat_name == "Bandt & Pompe":
                self.setup_bandt_pompe_controls(viewer_frame, subtab)
            elif stat_name == "IBI":
                self.setup_IBI_controls(viewer_frame,subtab)
            elif stat_name == "tau_d_heatmap":
                self.setup_tau_d_heatmap(viewer_frame,subtab)
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

    def setup_IBI_controls(self, viewer, subtab):
        controls_frame = subtab.controls_frame
        calc_controls = ttk.LabelFrame(controls_frame, text="Parámetros IBI y Visualización")
        calc_controls.pack(fill="x", padx=2, pady=4)
        fs_var = tk.DoubleVar()
        title_var = tk.StringVar(value="Intervalos Inter-Beat (IBI)")
        xlabel_var = tk.StringVar(value="Latido (n)")
        ylabel_var = tk.StringVar(value="IBI (ms)")
        try:
            fs_val = viewer.fs
            fs_var.set(fs_val)
            fs_label_text = f"Frecuencia Muestreo (FS): {fs_val} Hz"
            fs_entry_state = 'readonly'
        except (AttributeError, Exception):
            fs_label_text = "Frecuencia Muestreo (Hz):"
            fs_entry_state = 'normal'
        ttk.Label(calc_controls, text=fs_label_text).grid(row=0, column=0, padx=4, pady=2, sticky='e')
        fs_entry = ttk.Entry(calc_controls, textvariable=fs_var, width=10, state=fs_entry_state)
        fs_entry.grid(row=0, column=1, padx=4, pady=2, sticky='w')
        ttk.Label(calc_controls, text="Título Principal:").grid(row=1, column=0, padx=4, pady=2, sticky='e')
        ttk.Entry(calc_controls, textvariable=title_var, width=30).grid(row=1, column=1, padx=4, pady=2, columnspan=3, sticky='ew')
        ttk.Label(calc_controls, text="Título Eje X:").grid(row=2, column=0, padx=4, pady=2, sticky='e')
        ttk.Entry(calc_controls, textvariable=xlabel_var, width=15).grid(row=2, column=1, padx=4, pady=2, sticky='w')
        ttk.Label(calc_controls, text="Título Eje Y:").grid(row=2, column=2, padx=4, pady=2, sticky='e')
        ttk.Entry(calc_controls, textvariable=ylabel_var, width=15).grid(row=2, column=3, padx=4, pady=2, sticky='w')
        save_button_ref = ttk.Button(calc_controls, text="Guardar IBI (.mat)",
                                        command=lambda: self.save_ibi_to_mat(subtab.ibi_data if hasattr(subtab, 'ibi_data') else None),
                                        state='disabled')
        save_button_ref.grid(row=3, column=2, columnspan=2, pady=6, padx=4, sticky='ew')
        ttk.Button(calc_controls, text="Calcular IBI y Graficar",
                command=lambda: self.run_IBI(
                    subtab,
                    fs_var.get(),
                    title_var.get(),
                    xlabel_var.get(),
                    ylabel_var.get(),
                    save_button_ref
                )
                ).grid(row=3, column=0, columnspan=2, pady=6, padx=4, sticky='ew')

    def run_IBI(self, subtab, fs_value, title_text, xlabel_text, ylabel_text, save_button_ref):
        current_viewer = self.get_current_viewer()
        if current_viewer is None:
            messagebox.showerror("Error", "No se encontró un visor EDF o MAT en esta pestaña.")
            return
        signal = current_viewer.get_current_signal()
        if signal is None:
            messagebox.showinfo("Atención", "No hay señal seleccionada.")
            return
        try:
            fs = float(fs_value)
            if fs <= 0:
                raise ValueError("La frecuencia de muestreo debe ser un número positivo.")
        except ValueError as e:
            messagebox.showerror("Error FS", str(e))
            return
        try:
            ibi_data = calculate_ibi(
                raw_signal=signal,
                fs=fs,
                tab_ax=subtab.ax,
                tab_canvas=subtab.canvas,
                plot_style_var='default',
                title_var=title_text,
                xlabel_var=xlabel_text,
                ylabel_var=ylabel_text
            )
            subtab.ibi_data = ibi_data
            save_button_ref.config(state='normal')
        except Exception as e:
            messagebox.showerror("Error IBI", str(e))

    def save_ibi_to_mat(self, ibi_data):
        if ibi_data is None:
            messagebox.showinfo("Atención", "Primero debe calcular los datos IBI.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mat",
            filetypes=[("MATLAB files", "*.mat"), ("All Files", "*.*")],
            title="Guardar datos IBI como archivo .mat"
        )
        if not file_path:
            return
        try:
            data_dict = {"ibi_values_ms": ibi_data}
            savemat(file_path, data_dict)
            messagebox.showinfo("Éxito", f"Datos IBI guardados en:\n{file_path}")
        except ImportError:
            messagebox.showerror("Error de Importación", "La librería 'scipy' (scipy.io) es necesaria para guardar archivos .mat. Instálela con 'pip install scipy'.")
        except Exception as e:
            messagebox.showerror("Error al guardar", f"Ocurrió un error al guardar el archivo: {e}")

    ########################################################################################
    # ----------------- Tau (d) HeatMap -------------------------------------------------- #
    ########################################################################################
    def setup_tau_d_heatmap(self, viewer, subtab):

        controls_frame = subtab.controls_frame
        controls = ttk.LabelFrame(controls_frame, text="Parámetros para Tau(d): HeatMap")
        controls.pack(fill="x", padx=2, pady=4)

        fs_var = tk.DoubleVar()

        title_var = tk.StringVar(value="Tau(d) HeatMap")
        xlabel_var = tk.StringVar(value="Índice de ventana")
        ylabel_var = tk.StringVar(value="Frecuencia relativa")

        # Ejemplo de controles: retardo, dimensión embedding, paso, ventana
        ttk.Label(controls, text="Limite superior para Tau:").grid(row=0, column=0, padx=4, pady=2)
        tau_var_max = tk.IntVar(value=10)
        ttk.Spinbox(controls, from_=1, to=500, width=5, textvariable=tau_var_max).grid(row=0, column=1, padx=4)

        ttk.Label(controls, text="Dimensión embedding:").grid(row=0, column=2, padx=4, pady=2)
        dim_var = tk.IntVar(value=3)
        ttk.Spinbox(controls, from_=2, to=10, width=5, textvariable=dim_var).grid(row=0, column=3, padx=4)

        ttk.Label(controls, text="Paso:").grid(row=1, column=0, padx=4, pady=2)
        step_var = tk.IntVar(value=1)
        ttk.Spinbox(controls, from_=1, to=10, width=5, textvariable=step_var).grid(row=1, column=1, padx=4)

        ttk.Label(controls, text="Ventana:").grid(row=1, column=2, padx=4, pady=2)
        win_var = tk.IntVar(value=100)
        ttk.Spinbox(controls, from_=10, to=1000, width=6, textvariable=win_var).grid(row=1, column=3, padx=4)


        # Título
        ttk.Label(controls, text="Título Principal:").grid(
            row=2, column=0, padx=4, pady=2, sticky='e'
        )
        ttk.Entry(controls, textvariable=title_var, width=30).grid(
            row=2, column=1, padx=4, pady=2, columnspan=3, sticky='ew'
        )

        # Ejes
        ttk.Label(controls, text="Título Eje X:").grid(
            row=3, column=0, padx=4, pady=2, sticky='e'
        )
        ttk.Entry(controls, textvariable=xlabel_var, width=15).grid(
            row=3, column=1, padx=4, pady=2, sticky='w'
        )

        ttk.Label(controls, text="Título Eje Y:").grid(
            row=4, column=0, padx=4, pady=2, sticky='e'
        )
        ttk.Entry(controls, textvariable=ylabel_var, width=15).grid(
            row=4, column=1, padx=4, pady=2, sticky='w'
        )

        # Botón de guardado (deshabilitado inicialmente)
        save_button_ref = ttk.Button(
            controls,
            text="Guardar Tau(d) (.mat)",
            command=lambda: self.save_tau_d_heatmap_to_mat(
                subtab.tau_d_heatmap_data if hasattr(subtab, 'tau_d_heatmap_data') else None
            ),
            state='disabled'
        )
        save_button_ref.grid(row=5, column=3, columnspan=2, pady=6, padx=4, sticky='ew')

        # Botón principal: calcula tau(d) heatmap
        ttk.Button(controls, text="Calcular y Graficar",
            command=lambda: self.run_tau_d_heatmap(
                subtab,
                tau_var_max.get(),
                dim_var.get(),
                step_var.get(),
                win_var.get(),
                title_var.get(),
                xlabel_var.get(),
                ylabel_var.get(),
                save_button_ref
            )
        ).grid(row=3, column=0, columnspan=2, pady=6, padx=4, sticky='ew')

    def run_tau_d_heatmap(self, subtab, tau_max, dim, step, win, title_text, xlabel_text, ylabel_text, save_button_ref):

        current_viewer = self.get_current_viewer()
        if current_viewer is None:
            messagebox.showerror("Error", "No se encontró un visor EDF o MAT en esta pestaña.")
            return
        signal = current_viewer.get_current_signal()
        if signal is None:
            messagebox.showinfo("Atención", "No hay señal seleccionada.")
            return

        try:
            
            tau_d_heatmap_data = calculate_tau_d_heatmap(
                time_serie=signal,
                embeding=dim,
                delay_max= tau_max,  
                window= win, 
                step = step,

            )

            subtab.tau_d_heatmap_data = tau_d_heatmap_data
            save_button_ref.config(state='normal')
        except Exception as e:
            messagebox.showerror("Error tau_d_heatmap", str(e))
            return


        # ------------------------------------------------------------------
        # Graficar heatmap directamente en la subpestaña (sin crear figura)
        # ------------------------------------------------------------------

        ax = subtab.ax
        ax.clear()

        # matriz heatmap
        im = ax.imshow(
            tau_d_heatmap_data,
            cmap='jet',
            aspect='auto',
            origin='lower'
        )

        # colorbar incrustado en la subpestaña
        if hasattr(subtab, "colorbar") and subtab.colorbar is not None:
            subtab.colorbar.remove()

        subtab.colorbar = ax.figure.colorbar(im, ax=ax)

        # etiquetas
        ax.set_xlabel(xlabel_text)
        ax.set_ylabel(ylabel_text)
        ax.set_title(title_text)

        # refrescar gráfico
        subtab.canvas.draw()

