# Pixel Sorting Tool — Implementation Plan

## Context
Build a cross-platform PySide6 desktop app for interactive pixel sorting glitch art. Inspired by [DavidMcLaughlin208/PixelSorting](https://github.com/DavidMcLaughlin208/PixelSorting) (target goal) and [Akascape/Pixelort](https://github.com/Akascape/Pixelort) (reference). The target project uses C++/OpenFrameworks with real-time interaction, mask drawing, angle control, and video support. We'll replicate the core experience in Python/PySide6.

## Tech Stack
- **Python 3.10+**, **PySide6**, **numpy**, **Pillow**
- Optional later: **opencv-python** for video support

## Project Structure
```
PixelSorting/
├── main.py                    # Entry point
├── requirements.txt           # PySide6, Pillow, numpy
├── pixelsorting/
│   ├── __init__.py
│   ├── core/                  # Pure logic (no Qt)
│   │   ├── __init__.py
│   │   ├── sort_params.py     # SortParams dataclass + enums
│   │   ├── sort_keys.py       # Brightness, hue, saturation, etc.
│   │   ├── span_detector.py   # Threshold-based span finding
│   │   ├── sorting_engine.py  # Main pixel sorting algorithm
│   │   └── image_buffer.py    # numpy array wrapper + conversions
│   ├── ui/                    # All PySide6 widgets
│   │   ├── __init__.py
│   │   ├── main_window.py     # QMainWindow — menus, toolbar, wiring
│   │   ├── canvas_view.py     # QGraphicsView — pan, zoom, selection, mask painting
│   │   ├── canvas_scene.py    # QGraphicsScene — image + overlay layers
│   │   ├── settings_panel.py  # QDockWidget — all sort parameters
│   │   ├── coordinate_input.py# X/Y/W/H spin boxes
│   │   └── context_menu.py    # Right-click sort menu
│   └── commands/
│       ├── __init__.py
│       └── sort_command.py    # QUndoCommand for undo/redo
```

## Features (MVP)

### File Operations
- Open image (PNG, JPG, BMP, TIFF) via File menu or drag-and-drop
- Save / Save As
- Close image

### Canvas
- Pan (middle-click drag or hand tool)
- Zoom in/out (scroll wheel, anchored under cursor, +/- keys)
- Fit to window, reset zoom
- Status bar: cursor coordinates, zoom level, image dimensions

### Selection Methods
1. **Bounding box** — click-and-drag rectangle on canvas
2. **Coordinate input** — type X, Y, W, H directly (bidirectional sync with box)
3. **Freehand mask painting** — brush to paint where sorting applies (like both reference projects)

### Pixel Sorting Parameters (Settings Panel + Right-Click Menu)
| Parameter | Type | Description |
|-----------|------|-------------|
| Sort Direction | Combo | Horizontal, Vertical |
| Angle | Slider 0-360 | Arbitrary angle sorting (key feature from target) |
| Sort Key | Combo | Brightness, Hue, Saturation, Intensity, Minimum, R/G/B channel |
| Interval Mode | Combo | Threshold, Random, Edges, Waves, None (full row) |
| Lower Threshold | Slider 0.0-1.0 | Min brightness for span inclusion |
| Upper Threshold | Slider 0.0-1.0 | Max brightness for span inclusion |
| Pixel Size | SpinBox 1-32 | Block size (NxN super-pixels) |
| Span Width (min) | SpinBox | Skip spans shorter than this |
| Span Length (max) | SpinBox | Cap maximum span length |
| Jitter | Slider 0-100 | Random displacement after sorting |
| Reverse | Checkbox | Flip sort order |

### Preview & Apply
- Live preview on a background QThread (debounced 300ms)
- "Apply" commits via undo stack
- "Reset" restores defaults

### Undo/Redo
- Region-based snapshots (only store affected bounding box, not full image)
- Ctrl+Z / Ctrl+Y

## Core Algorithm

### Span Detection
For each row/column in the selected region:
1. Compute brightness values for all pixels
2. Find contiguous runs where brightness is within [lower, upper] threshold
3. Filter by min span width, cap by max span length
4. Use vectorized numpy (np.diff on boolean mask) for performance

### Sorting
For each detected span:
1. Compute sort key values (brightness, hue, etc.)
2. np.argsort to get sorted indices
3. Apply jitter displacement if > 0
4. Write sorted pixels back

### Angle Support
Rotate the image by the specified angle before sorting horizontally, then rotate back. This gives arbitrary-angle sorting with minimal algorithm complexity.

### Pixel Size (Block Mode)
Downsample image into NxN blocks (average), sort the blocks, then upsample back.

## Implementation Order

### Phase 1: Core engine (no UI)
1. `sort_params.py` — dataclass + enums
2. `sort_keys.py` — brightness, hue, saturation, intensity, minimum, channels
3. `span_detector.py` — threshold-based span finding
4. `sorting_engine.py` — sort_region(), sort_line(), jitter, block mode, angle rotation
5. `image_buffer.py` — numpy wrapper, file I/O via Pillow, QPixmap conversion

### Phase 2: Basic UI shell
6. `main.py` + `main_window.py` — window, menus (Open/Save/Close), toolbar, status bar
7. `canvas_scene.py` + `canvas_view.py` — display image, pan, zoom
8. Wire file open/save through ImageBuffer

### Phase 3: Selection + Settings
9. Bounding box selection overlay on canvas
10. `coordinate_input.py` — spin boxes synced with canvas selection
11. `settings_panel.py` — all parameter widgets
12. `context_menu.py` — right-click quick access

### Phase 4: Sort integration
13. `sort_command.py` — QUndoCommand with region snapshots
14. Wire Apply button: extract region -> engine.sort_region() -> push undo command -> refresh
15. Wire undo/redo to canvas refresh

### Phase 5: Preview + mask painting
16. Background QThread worker for live preview
17. Preview overlay layer on canvas
18. Freehand mask painting mode (brush tool)

### Phase 6: Polish
19. Drag-and-drop file loading
20. Keyboard shortcuts (Ctrl+O, Ctrl+S, Ctrl+Z, Ctrl+Y, +/-, Esc)
21. Unsaved changes warning on close
22. Window state persistence via QSettings

## Verification
1. Run `python main.py` — window opens, no crashes
2. Open a test image — displays correctly, pan/zoom works
3. Draw bounding box — coordinates update, overlay visible
4. Type coordinates — overlay updates on canvas
5. Adjust settings + click Apply — pixels sort within selection
6. Ctrl+Z undoes, Ctrl+Y redoes
7. Preview toggle shows live-updating sort effect
8. Right-click context menu works
9. Save outputs correct image with sorted regions baked in
