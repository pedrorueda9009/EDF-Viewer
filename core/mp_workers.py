from multiprocessing import Process, Queue
import numpy as np
from core.estadisticas import band_and_pompe
from core.estadisticas import calculate_tau_d_heatmap
from core.estadisticas import patrones_apilados


def worker_patrones_apilados(signal, dim, tau, win, step, queue):
    
    try:
        # debe primero calcular entropia bandt and pompe
        freqs, Hnorm, times = band_and_pompe(
            signal, dim, tau, win, step,
            graf=False, beat_times=None
        )

        n_windows, n_patterns, cum, indices, mid, colors, handles = patrones_apilados(
            freqs,
            dim
        )

        queue.put(("ok", (n_windows, n_patterns, cum, indices, mid, colors, handles)))

    except Exception as e:
        
        queue.put(("error", str(e)))


def worker_bandt_pompe(signal, dim, tau, win, step, queue):
    try:

        freqs, Hnorm, times = band_and_pompe(
            signal, dim, tau, win, step,
            graf=False, beat_times=None
        )
        queue.put(("ok", (freqs, Hnorm, times)))
    except Exception as e:
        queue.put(("error", str(e)))


def worker_tau_d_heatmap(signal, embeding, delay_max, window, step, queue):
    try:
        result = calculate_tau_d_heatmap(
            time_serie=signal,
            embeding=embeding,
            delay_max=delay_max,
            window=window,
            step=step
        )
        queue.put(("ok", result))
    except Exception as e:
        queue.put(("error", str(e)))
