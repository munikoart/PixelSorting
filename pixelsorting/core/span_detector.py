from typing import List, Tuple

import numpy as np

from .sort_keys import compute_brightness
from .sort_params import IntervalMode


def detect_spans(
    pixels: np.ndarray,
    mode: IntervalMode,
    lower: float,
    upper: float,
    span_min: int,
    span_max: int,
) -> List[Tuple[int, int]]:
    """Find contiguous spans of pixels to sort.

    Args:
        pixels: (N, 3+) uint8 pixel array for one row/column
        mode: interval detection mode
        lower: lower threshold (0-1)
        upper: upper threshold (0-1)
        span_min: minimum span length (skip shorter)
        span_max: maximum span length (0 = unlimited)

    Returns:
        List of (start, end) index tuples (end is exclusive)
    """
    n = len(pixels)
    if n == 0:
        return []

    if mode == IntervalMode.NONE:
        spans = [(0, n)]
    elif mode == IntervalMode.THRESHOLD:
        spans = _threshold_spans(pixels, lower, upper)
    elif mode == IntervalMode.RANDOM:
        spans = _random_spans(n)
    elif mode == IntervalMode.EDGES:
        spans = _edge_spans(pixels)
    elif mode == IntervalMode.WAVES:
        spans = _wave_spans(n)
    else:
        spans = [(0, n)]

    # Filter by min length
    if span_min > 1:
        spans = [(s, e) for s, e in spans if (e - s) >= span_min]

    # Cap by max length
    if span_max > 0:
        capped = []
        for s, e in spans:
            while s < e:
                end = min(s + span_max, e)
                capped.append((s, end))
                s = end
            spans = capped

    return spans


def _threshold_spans(
    pixels: np.ndarray, lower: float, upper: float
) -> List[Tuple[int, int]]:
    brightness = compute_brightness(pixels)
    mask = (brightness >= lower) & (brightness <= upper)
    return _mask_to_spans(mask)


def _random_spans(n: int) -> List[Tuple[int, int]]:
    rng = np.random.default_rng()
    spans = []
    i = 0
    while i < n:
        length = rng.integers(10, max(11, n // 4))
        end = min(i + int(length), n)
        spans.append((i, end))
        gap = rng.integers(1, max(2, 20))
        i = end + int(gap)
    return spans


def _edge_spans(pixels: np.ndarray) -> List[Tuple[int, int]]:
    brightness = compute_brightness(pixels)
    if len(brightness) < 2:
        return [(0, len(brightness))]

    edges = np.abs(np.diff(brightness))
    threshold = np.mean(edges) + np.std(edges)
    edge_mask = edges > threshold
    edge_positions = np.where(edge_mask)[0] + 1

    positions = np.concatenate(([0], edge_positions, [len(brightness)]))
    spans = []
    for i in range(len(positions) - 1):
        s, e = int(positions[i]), int(positions[i + 1])
        if e > s:
            spans.append((s, e))
    return spans


def _wave_spans(n: int) -> List[Tuple[int, int]]:
    wave_len = max(10, n // 8)
    spans = []
    i = 0
    phase = 0
    while i < n:
        length = int(wave_len * (0.5 + 0.5 * np.sin(phase)))
        length = max(2, length)
        end = min(i + length, n)
        spans.append((i, end))
        i = end
        phase += 0.5
    return spans


def _mask_to_spans(mask: np.ndarray) -> List[Tuple[int, int]]:
    """Convert boolean mask to list of (start, end) spans."""
    if len(mask) == 0:
        return []

    padded = np.empty(len(mask) + 2, dtype=bool)
    padded[0] = False
    padded[-1] = False
    padded[1:-1] = mask

    diff = np.diff(padded.astype(np.int8))
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]

    return list(zip(starts.tolist(), ends.tolist()))
