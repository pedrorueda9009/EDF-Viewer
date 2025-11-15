import numpy as np


def arr_summary(value, maxitems=6):
    """Resumen simple del contenido de una variable."""
    if isinstance(value, np.ndarray):
        flat = value.flatten()
        snippet = ", ".join(map(str, flat[:maxitems]))
        return f"ndarray shape={value.shape}, dtype={value.dtype}, data=[{snippet}{'...' if value.size > maxitems else ''}]"
    else:
        return repr(value)[:200]
