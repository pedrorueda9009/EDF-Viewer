#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MatViewer Simple
Autor: Pedro Enrique Rueda
"""

from ui.main_window import MainWindow
import tkinter as tk

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
