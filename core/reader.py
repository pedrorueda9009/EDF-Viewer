import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from scipy.io import loadmat
import mne
from scipy.io import savemat


try:
    import h5py
    HAS_H5PY = True
except Exception:
    HAS_H5PY = False


def read_mat_safely(path):
    """Lee un archivo .mat y devuelve un dict con sus variables."""
    try:
        data = loadmat(path, simplify_cells=True)
        return data
    except Exception:
        if HAS_H5PY:
            try:
                data = {}
                with h5py.File(path, 'r') as f:
                    def visit(name, obj):
                        if isinstance(obj, h5py.Dataset):
                            try:
                                data[name] = obj[()]
                            except Exception:
                                pass
                    f.visititems(visit)
                return data
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo .mat:\n{e}")
        else:
            messagebox.showerror("Error", "Archivo .mat no compatible y h5py no instalado.")
        return None