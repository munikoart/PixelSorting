import numpy as np
from PIL import Image

from .sort_keys import compute_sort_values
from .sort_params import SortDirection, SortParams
from .span_detector import detect_spans


def sort_region(
    image: np.ndarray,
    params: SortParams,
    x: int = 0,
    y: int = 0,
    w: int = 0,
    h: int = 0,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Sort pixels in a region of the image.

    Args:
        image: (H, W, 3) or (H, W, 4) uint8 array
        params: sorting parameters
        x, y, w, h: bounding box (0,0,0,0 = full image)
        mask: optional boolean mask same size as region (True = include)

    Returns:
        Copy of image with sorted region
    """
    result = image.copy()
    img_h, img_w = image.shape[:2]

    if w == 0 or h == 0:
        x, y, w, h = 0, 0, img_w, img_h

    # Clamp to image bounds
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = min(w, img_w - x)
    h = min(h, img_h - y)

    region = result[y : y + h, x : x + w].copy()

    # Handle angle rotation
    if params.angle != 0 and params.direction == SortDirection.HORIZONTAL:
        region, region_mask = _rotate_region(region, params.angle, mask)
        region = _sort_2d(region, params, region_mask)
        region = _unrotate_region(region, params.angle, (h, w, image.shape[2]))
        if mask is not None:
            mask_region = mask[:h, :w]
            for c in range(region.shape[2]):
                result[y : y + h, x : x + w, c] = np.where(
                    mask_region, region[:, :, c], result[y : y + h, x : x + w, c]
                )
        else:
            result[y : y + h, x : x + w] = region[:h, :w]
    else:
        region = _sort_2d(region, params, mask)
        result[y : y + h, x : x + w] = region[:h, :w]

    return result


def _sort_2d(
    region: np.ndarray,
    params: SortParams,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Sort a 2D region row-by-row or column-by-column."""
    result = region.copy()

    if params.direction == SortDirection.VERTICAL:
        result = np.rot90(result, 1)
        if mask is not None:
            mask = np.rot90(mask, 1)

    rows, cols = result.shape[:2]
    for row_idx in range(rows):
        row = result[row_idx]
        row_mask = mask[row_idx] if mask is not None else None
        result[row_idx] = _sort_line(row, params, row_mask)

    if params.direction == SortDirection.VERTICAL:
        result = np.rot90(result, -1)

    return result


def _sort_line(
    pixels: np.ndarray,
    params: SortParams,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Sort a single row of pixels according to params."""
    result = pixels.copy()
    n = len(pixels)
    if n == 0:
        return result

    bs = params.pixel_size
    if bs > 1:
        return _sort_line_blocked(pixels, params, mask)

    spans = detect_spans(
        pixels,
        params.interval_mode,
        params.lower_threshold,
        params.upper_threshold,
        params.span_min,
        params.span_max,
    )

    for start, end in spans:
        if mask is not None:
            span_mask = mask[start:end]
            if not np.any(span_mask):
                continue
            masked_indices = np.where(span_mask)[0]
            span_pixels = pixels[start:end][masked_indices]
        else:
            span_pixels = pixels[start:end]

        if len(span_pixels) < 2:
            continue

        values = compute_sort_values(span_pixels, params.sort_key)
        order = np.argsort(values)
        if params.reverse:
            order = order[::-1]

        sorted_pixels = span_pixels[order]

        if params.jitter > 0:
            sorted_pixels = _apply_jitter(sorted_pixels, params.jitter)

        if mask is not None:
            for i, idx in enumerate(masked_indices):
                result[start + idx] = sorted_pixels[i]
        else:
            result[start:end] = sorted_pixels

    return result


def _sort_line_blocked(
    pixels: np.ndarray,
    params: SortParams,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Sort groups of pixel_size pixels as units, preserving original pixels."""
    result = pixels.copy()
    n = len(pixels)
    bs = params.pixel_size
    n_groups = n // bs

    if n_groups < 2:
        return result

    # Build groups of bs consecutive pixels
    groups = []
    group_keys = []
    for g in range(n_groups):
        s = g * bs
        e = s + bs
        group = pixels[s:e].copy()
        groups.append(group)
        # Sort key is the mean value across all pixels in the group
        vals = compute_sort_values(group, params.sort_key)
        group_keys.append(vals.mean())

    group_keys = np.array(group_keys)

    # Detect spans at the group level using a params copy with adjusted thresholds
    # Build a "representative pixel" array for span detection (one per group)
    rep_pixels = np.array([g.mean(axis=0).astype(np.uint8) for g in groups])
    spans = detect_spans(
        rep_pixels,
        params.interval_mode,
        params.lower_threshold,
        params.upper_threshold,
        max(1, params.span_min // bs),
        params.span_max // bs if params.span_max > 0 else 0,
    )

    for span_start, span_end in spans:
        if mask is not None:
            # Check if any pixel in these groups is masked
            px_start = span_start * bs
            px_end = span_end * bs
            if not np.any(mask[px_start:px_end]):
                continue

        span_keys = group_keys[span_start:span_end]
        if len(span_keys) < 2:
            continue

        order = np.argsort(span_keys)
        if params.reverse:
            order = order[::-1]

        # Apply jitter at group level
        if params.jitter > 0:
            rng = np.random.default_rng()
            jitter_groups = max(1, params.jitter // bs)
            shuffled = order.copy()
            for i in range(len(shuffled)):
                offset = rng.integers(-jitter_groups, jitter_groups + 1)
                j = max(0, min(len(shuffled) - 1, i + offset))
                shuffled[i], shuffled[j] = order[j], order[i]
            order = shuffled

        sorted_groups = [groups[span_start + idx] for idx in order]
        for i, sg in enumerate(sorted_groups):
            dst = (span_start + i) * bs
            result[dst : dst + bs] = sg

    return result


def _apply_jitter(pixels: np.ndarray, jitter: int) -> np.ndarray:
    """Randomly displace sorted pixels by up to jitter amount."""
    n = len(pixels)
    rng = np.random.default_rng()
    result = pixels.copy()
    for i in range(n):
        offset = rng.integers(-jitter, jitter + 1)
        j = max(0, min(n - 1, i + offset))
        result[i], result[j] = pixels[j].copy(), pixels[i].copy()
    return result



def _rotate_region(
    region: np.ndarray, angle: float, mask: np.ndarray | None = None
) -> tuple:
    """Rotate region by angle degrees for angled sorting."""
    pil_img = Image.fromarray(region)
    rotated = pil_img.rotate(-angle, resample=Image.BILINEAR, expand=True)
    rotated_arr = np.array(rotated)

    rotated_mask = None
    if mask is not None:
        pil_mask = Image.fromarray((mask * 255).astype(np.uint8))
        rotated_mask_img = pil_mask.rotate(-angle, resample=Image.NEAREST, expand=True)
        rotated_mask = np.array(rotated_mask_img) > 127
    return rotated_arr, rotated_mask


def _unrotate_region(
    region: np.ndarray, angle: float, original_shape: tuple
) -> np.ndarray:
    """Rotate back to original orientation and crop to original size."""
    oh, ow, oc = original_shape
    pil_img = Image.fromarray(region)
    unrotated = pil_img.rotate(angle, resample=Image.BILINEAR, expand=True)
    arr = np.array(unrotated)

    # Crop center to original size
    rh, rw = arr.shape[:2]
    cy, cx = rh // 2, rw // 2
    y0 = max(0, cy - oh // 2)
    x0 = max(0, cx - ow // 2)
    cropped = arr[y0 : y0 + oh, x0 : x0 + ow]

    # Pad if needed
    if cropped.shape[0] < oh or cropped.shape[1] < ow:
        padded = np.zeros((oh, ow, oc), dtype=np.uint8)
        ph = min(cropped.shape[0], oh)
        pw = min(cropped.shape[1], ow)
        padded[:ph, :pw] = cropped[:ph, :pw]
        return padded

    return cropped[:oh, :ow]
