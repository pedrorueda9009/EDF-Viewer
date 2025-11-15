#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MatViewer Simple
Versión reducida y limpia: muestra contenido de archivos .mat
Autor: ChatGPT (versión adaptada para uso práctico)
"""

from ui.main_window import MainWindow
import tkinter as tk

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
