import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from core.summarizer import arr_summary

# ---------------------------
# Ventana detalle de variable
# ---------------------------
class VarDetailWindow(tk.Toplevel):
    def __init__(self, master, name, value):
        super().__init__(master)
        self.title(f"Variable: {name}")
        self.geometry("900x600")

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        if isinstance(value, np.ndarray):
            self.show_array(frame, value)
        else:
            txt = tk.Text(frame, wrap="none")
            txt.insert("1.0", arr_summary(value, maxitems=20))
            txt.config(state="disabled")
            txt.grid(row=0, column=0, sticky="nsew")
            sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            sb.grid(row=0, column=1, sticky="ns")


    def show_array(self, parent, arr, maxrows=100, maxcols=20):
        """Muestra un array NumPy como tabla con scroll, numeración y opción de graficar."""
        self.arr_full = arr  # Guardar el array completo para usarlo en la gráfica

        # --- Convertir a DataFrame (solo vista parcial para velocidad) ---
        if arr.ndim == 1:
            df = pd.DataFrame(arr, columns=["Columna"])
        elif arr.ndim == 2:
            nr = min(arr.shape[0], maxrows)
            nc = min(arr.shape[1], maxcols)
            df = pd.DataFrame(arr[:nr, :nc])
        else:
            reshaped = arr.reshape(arr.shape[0], -1)
            nr = min(reshaped.shape[0], maxrows)
            nc = min(reshaped.shape[1], maxcols)
            df = pd.DataFrame(reshaped[:nr, :nc])

        # --- Agregar numeración de filas ---
        # df.insert(0, "Fila", range(1, len(df) + 1))
        df.insert(0, "Fila", np.arange(1, len(df) + 1, dtype=int))

        # --- Botón para graficar ---
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        plot_btn = ttk.Button(btn_frame, text="Graficar selección", command=self.plot_selected_row)
        plot_btn.pack(side="left", padx=5, pady=2)

        # --- Tabla ---
        cols = list(map(str, df.columns))
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=20)

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=80 if c != "Fila" else 60, anchor="center")

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))

        # --- Scrollbars ---
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

    def plot_selected_row(self):
        """Grafica la fila seleccionada o el array completo como señal."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Atención", "Por favor, selecciona una fila para graficar.")
            return

        fila = int(float(self.tree.item(selection[0], "values")[0])) - 1  # índice real (0-based)
        arr = self.arr_full

        try:
            # --- Señal 1D (una sola serie temporal) ---
            if arr.ndim == 1:
                y = arr
                x = np.arange(len(y))
                plt.figure(figsize=(10, 4))
                plt.plot(x, y, color='tabblue')
                plt.title("Señal (1D)")
                plt.xlabel("Índice")
                plt.ylabel("Valor")
                plt.grid(True)
                plt.tight_layout()
                plt.show()

            # --- Señal 2D: múltiples canales o repeticiones ---
            elif arr.ndim == 2:
                if fila < arr.shape[0]:
                    y = arr[fila, :]
                    x = np.arange(len(y))
                    plt.figure(figsize=(10, 4))
                    plt.plot(x, y, color='taborange')
                    plt.title(f"Señal - Fila {fila+1}")
                    plt.xlabel("Muestras")
                    plt.ylabel("Amplitud")
                    plt.grid(True)
                    plt.tight_layout()
                    plt.show()
                else:
                    messagebox.showerror("Error", f"La fila {fila+1} está fuera del rango del array.")

            # --- Arrays con más dimensiones ---
            else:
                # Aplanamos el primer eje para visualizar algo útil
                y = arr.reshape(arr.shape[0], -1)[fila, :]
                plt.figure(figsize=(10, 4))
                plt.plot(y, color='tabgreen')
                plt.title(f"Señal (fila {fila+1}) de un array {arr.shape}")
                plt.xlabel("Índice")
                plt.ylabel("Valor")
                plt.grid(True)
                plt.tight_layout()
                plt.show()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo graficar: {e}")
