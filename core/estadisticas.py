import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from itertools import permutations
import math
import os
from scipy.io import loadmat
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, medfilt, butter, filtfilt

def ordinal_patterns(series, D, tau):
    """
    Devuelve lista de tuplas con el patrón ordinal para cada embedding disponible.
    Las tuplas son la permutación de posiciones: por ejemplo (2,1,0).
    Usamos np.argsort(..., kind='mergesort') para mantener estabilidad (rompe empates por orden).
    """
    N = len(series)
    m = D
    max_shift = (m - 1) * tau
    patterns = []
    for i in range(0, N - max_shift):
        # construir vector embebido
        vec = series[i : i + (m - 1)*tau + 1 : tau]
        # índice de orden ascendente (0..D-1) con mergesort estable para tratamiento de empates
        order = tuple(np.argsort(vec, kind='mergesort'))
        patterns.append(order)
    return patterns


def validar_parametros(time_serie, embeding, window, step):
    if len(time_serie) < embeding:
        raise ValueError("La serie es demasiado corta para el embedding indicado.")
    if window > len(time_serie):
        raise ValueError("El tamaño de ventana excede la longitud de la serie.")
    if step <= 0:
        raise ValueError("El paso entre ventanas debe ser mayor que cero.")


def band_and_pompe(time_serie, embeding, delay, window, step,
                   graf, beat_times=None, plot=False, paso_ejeT=10,
                   paso_color=10, color1='red', color2='blue',
                   ruta_guardar='/', output_graf='/'):

    # Validaciones
    validar_parametros(time_serie, embeding, window, step)

    # Crear patrones ordinales posibles
    all_perms = list(permutations(range(embeding)))
    perm_to_index = {perm: idx for idx, perm in enumerate(all_perms)}
    n_patterns = math.factorial(embeding)

    freqs_list = []
    H_norm = []
    win_times = []

    # Índices de inicio de cada ventana
    start_indices = list(range(0, len(time_serie) - window + 1, step))
    if len(start_indices) == 0:
        raise ValueError("Con win_size y la longitud de IBI no se forma ninguna ventana. Reduce win_size o cambia step.")

    for start in start_indices:
        segment = time_serie[start : start + window]
        
        pats = ordinal_patterns(segment, embeding, delay)

        # Calcular distribución de patrones
        if len(pats) == 0:
            p_vec = np.zeros(n_patterns)
            Hn = 0.0
        else:
            counts = np.zeros(n_patterns, dtype=float)
            for p in pats:
                idx = perm_to_index[p]
                counts[idx] += 1.0

            p_vec = counts / counts.sum()
            p_nonzero = p_vec[p_vec > 0]
            H = -np.sum(p_nonzero * np.log(p_nonzero))
            Hn = H / np.log(math.factorial(embeding))

        # Manejo seguro de beat_times
        if beat_times is None:
            # valor por defecto (tiempo relativo)
            win_times.append(start)
        else:
            # valor original si existe beat_times real
            bt = np.asarray(beat_times)
            if len(bt) >= start + window:
                win_times.append(np.mean(bt[start:start+window]))
            else:
                # Si beat_times es más corto, evitar crash
                win_times.append(np.nan)

        freqs_list.append(p_vec)
        H_norm.append(Hn)

    # === GRAFICADOS (idénticos a tu código original, sin tocar) ===
    if graf and plot and beat_times is not None:
        # todo este bloque queda EXACTO, no lo modifico
        ibi = np.asarray(time_serie)
        tiempos_ibi = np.asarray(beat_times)[1:]
        index = np.arange(len(ibi))

        fig, ax1 = plt.subplots(figsize=(17, 8))
        ax1.plot(index, ibi, marker='o', color='tab:blue', linewidth=1)
        ax1.set_xlabel("Índice del intervalo")
        ax1.set_ylabel("IBI (s)")
        ax1.set_title("IBI vs índice con eje superior de tiempo (coloreado)")
        ax1.grid(True, linestyle='--', alpha=0.5)

        ax2 = ax1.twiny()
        ax2.set_xlim(ax1.get_xlim())
        ax2.set_xticks(index[::paso_ejeT]) 
        ax2.set_xticklabels([f"{t:.2f}" for t in tiempos_ibi[::paso_ejeT]])
        ax2.set_xlabel("Tiempo (s)")

        color_ventana = paso_color
        max_t = tiempos_ibi[-1]
        t_limit = 0
        color = True

        while t_limit < max_t:
            next_t = t_limit + color_ventana
            color_name = color1 if color else color2
            mask = (tiempos_ibi >= t_limit) & (tiempos_ibi < next_t)
            if np.any(mask):
                start_idx = np.where(mask)[0][0]
                end_idx = np.where(mask)[0][-1]
                ax1.axvspan(start_idx, end_idx, color=color_name, alpha=0.3)
            t_limit = next_t
            color = not color

        fig_path = os.path.join(output_graf, f'{ruta_guardar}_bib_d{embeding}_tau{delay}.png')
        plt.savefig(fig_path, dpi=200)
        plt.tight_layout()
        plt.close()

    return np.array(freqs_list), np.array(H_norm), np.array(win_times)

################################################################################
# Funciones para calcular el IBI
################################################################################
def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    """Filtro pasa banda Butterworth."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    y = filtfilt(b, a, data)
    return y

def detect_r_peaks(signal, fs):
    """
    Detecta picos R robustamente en una señal de ECG filtrada.
    
    Args:
        signal (np.array): Señal de ECG bruta.
        fs (float): Frecuencia de muestreo.
        
    Returns:
        np.array: Índices de los picos detectados.
    """
    # 1. Pre-procesamiento: Filtrado de la señal para enfatizar picos R
    # Frecuencias típicas para ECG: 5 a 15 Hz
    filtered_signal = butter_bandpass_filter(signal, 5, 15, fs, order=3)
    
    # 2. Rectificación y suavizado (para hacer los picos más obvios)
    processed_signal = np.abs(filtered_signal)
    # Filtro de media móvil (medfilt) para suavizar
    processed_signal = medfilt(processed_signal, kernel_size=int(fs/5) | 1) # kernel debe ser impar

    # 3. Detección de picos
    # Calculamos la distancia mínima entre picos (basado en un ritmo cardíaco máximo de 200 BPM)
    min_peak_distance = fs / 200 * 60 
    
    # Usamos find_peaks de Scipy
    # height: encuentra picos por encima de un umbral (media + std)
    # distance: distancia mínima requerida entre picos
    peaks_indices, _ = find_peaks(
        processed_signal, 
        height=np.mean(processed_signal) + np.std(processed_signal), 
        distance=min_peak_distance
    )
    
    return peaks_indices


# def calculate_ibi(raw_signal, fs, tab_ax, tab_canvas, plot_style_var, title_var):
#     """
#     Calcula los IBI a partir de la señal bruta (detectando picos R), 
#     grafica y actualiza el canvas de Tkinter.
#     """
#     if len(raw_signal) < fs * 2: # Se necesitan al menos 2 segundos de datos
#         raise ValueError("La señal es demasiado corta para calcular IBI.")

#     # 1. Detectar picos R
#     peaks_indices = detect_r_peaks(raw_signal, fs)
    
#     if len(peaks_indices) < 2:
#         raise ValueError("No se pudieron detectar suficientes picos R en la señal para calcular IBI.")

#     # 2. Calcular tiempos de picos en segundos
#     peak_times_seconds = peaks_indices / fs

#     # 3. Calcular IBI (diferencia entre tiempos consecutivos)
#     ibi_values_seconds = np.diff(peak_times_seconds)
#     ibi_values_ms = ibi_values_seconds * 1000 # Convertir a milisegundos

#     # --- Lógica de Graficación ---
#     plt.style.use(plot_style_var)
#     tab_ax.clear()
    
#     # Graficamos los IBI en ms
#     tab_ax.plot(ibi_values_ms, marker='o', linestyle='-', markersize=4, linewidth=1)
    
#     tab_ax.set_title(title_var)
#     tab_ax.set_xlabel("Latido (n)")
#     tab_ax.set_ylabel("IBI (ms)") # Ahora es fijo en MS
#     tab_ax.grid(True)
#     tab_canvas.draw()
    
#     plt.style.use('default') # Revertir estilo

#     return ibi_values_ms

def calculate_ibi(raw_signal, fs, tab_ax, tab_canvas, plot_style_var, title_var, xlabel_var, ylabel_var):
    """
    Calcula los IBI a partir de la señal bruta (detectando picos R), 
    grafica y actualiza el canvas de Tkinter con títulos de ejes personalizados.
    """
    if len(raw_signal) < fs * 2:
        raise ValueError("La señal es demasiado corta para calcular IBI.")

    # 1. Detectar picos R (usando la función de arriba)
    peaks_indices = detect_r_peaks(raw_signal, fs)
    
    if len(peaks_indices) < 2:
        raise ValueError("No se pudieron detectar suficientes picos R en la señal para calcular IBI.")

    # 2. Calcular tiempos de picos y IBI en milisegundos
    peak_times_seconds = peaks_indices / fs
    ibi_values_seconds = np.diff(peak_times_seconds)
    ibi_values_ms = ibi_values_seconds * 1000 

    # --- Lógica de Graficación ---
    plt.style.use(plot_style_var) # style_var será 'default' ahora
    tab_ax.clear()
    
    tab_ax.plot(ibi_values_ms, marker='o', linestyle='-', markersize=4, linewidth=1)
    
    # Usamos los parámetros de título y ejes pasados por el usuario
    tab_ax.set_title(title_var)
    tab_ax.set_xlabel(xlabel_var) 
    tab_ax.set_ylabel(ylabel_var) 
    tab_ax.grid(True)
    tab_canvas.draw()
    
    plt.style.use('default') 

    # Devolvemos los datos por si se quieren guardar
    return ibi_values_ms