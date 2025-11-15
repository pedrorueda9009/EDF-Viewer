mat_viewer/
│
├── main.py                       # Punto de entrada principal de la app (solo arranca la GUI)
│
├── core/
│   ├── __init__.py
│   ├── file_loader.py            # Carga de archivos (.mat, .edf)
│   ├── data_summary.py           # Resumen de variables y estructuras
│   ├── plot_utils.py             # Funciones genéricas de graficación
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py            # Ventana principal: selector de archivos
│   ├── var_detail_window.py      # Ventana detalle de variables .mat
│   ├── edf_viewer_window.py      # Ventana para archivos .edf
│
└── assets/
    ├── icons/                    # Íconos o imágenes (opcional)
    └── styles/                   # Temas visuales o CSS si usas ttkbootstrap en el futuro
