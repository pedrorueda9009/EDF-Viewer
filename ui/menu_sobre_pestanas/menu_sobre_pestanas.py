import tkinter as tk

class MenuSobrePestanas:
    def __init__(self,mainwindow, root, notebook):
        self.mainwindow = mainwindow
        self.root = root
        self.notebook = notebook
        self._tab_to_close = None
        self._build_menu()

    def _build_menu(self):

        # Vincular clic derecho sobre las pestañas
        self.notebook.bind("<Button-3>", self._show_tab_menu)

        # Menú contextual: aparece la opcion cerrar te da la opción de cerrar.
        self.tab_menu = tk.Menu(self.root, tearoff=0)
        self.tab_menu.add_command(label="Cerrar pestaña", command=self._close_current_tab)

    def _show_tab_menu(self, event):
        """Muestra el menú contextual sobre la pestaña clickeada."""
        # Identificar pestaña bajo el puntero
        clicked_tab = self.notebook.index(f"@{event.x},{event.y}")
        if clicked_tab < 0:
            return

        # Guardar pestaña seleccionada para cerrar luego
        self._tab_to_close = clicked_tab

        # Mostrar menú contextual
        self.tab_menu.tk_popup(event.x_root, event.y_root)

    def _close_current_tab(self):
        """Cierra la pestaña seleccionada vía menú contextual."""
        if hasattr(self, "_tab_to_close"):
            try:
                self.notebook.forget(self._tab_to_close)
            except Exception:
                pass
