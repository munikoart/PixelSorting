import numpy as np

from .sort_params import SortKey


def compute_sort_values(pixels: np.ndarray, key: SortKey) -> np.ndarray:
    """Compute sort key values for a 1D array of pixels.

    Args:
        pixels: shape (N, 3) or (N, 4) uint8 RGB(A) array
        key: which property to sort by

    Returns:
        1D float array of length N with the sort values
    """
    r = pixels[:, 0].astype(np.float32)
    g = pixels[:, 1].astype(np.float32)
    b = pixels[:, 2].astype(np.float32)

    if key == SortKey.BRIGHTNESS:
        return 0.299 * r + 0.587 * g + 0.114 * b

    if key == SortKey.INTENSITY:
        return (r + g + b) / 3.0

    if key == SortKey.MINIMUM:
        return np.minimum(np.minimum(r, g), b)

    if key == SortKey.RED:
        return r

    if key == SortKey.GREEN:
        return g

    if key == SortKey.BLUE:
        return b

    if key == SortKey.HUE:
        return _compute_hue(r, g, b)

    if key == SortKey.SATURATION:
        return _compute_saturation(r, g, b)

    return 0.299 * r + 0.587 * g + 0.114 * b


def compute_brightness(pixels: np.ndarray) -> np.ndarray:
    """Compute brightness for threshold detection. pixels shape (N, 3+)."""
    r = pixels[:, 0].astype(np.float32)
    g = pixels[:, 1].astype(np.float32)
    b = pixels[:, 2].astype(np.float32)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def _compute_hue(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c

    hue = np.zeros_like(r)
    mask = delta > 0

    # Red is max
    m = mask & (max_c == r)
    hue[m] = 60.0 * (((g[m] - b[m]) / delta[m]) % 6)

    # Green is max
    m = mask & (max_c == g)
    hue[m] = 60.0 * (((b[m] - r[m]) / delta[m]) + 2)

    # Blue is max
    m = mask & (max_c == b)
    hue[m] = 60.0 * (((r[m] - g[m]) / delta[m]) + 4)

    return hue


def _compute_saturation(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c

    sat = np.zeros_like(r)
    mask = max_c > 0
    sat[mask] = delta[mask] / max_c[mask]
    return sat
