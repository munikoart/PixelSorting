import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QUndoCommand

from ..core.image_buffer import ImageBuffer
from ..core.sort_params import SortParams
from ..core.sorting_engine import sort_region


class SortCommand(QUndoCommand):
    """Undoable pixel sort command with region-based snapshots."""

    def __init__(
        self,
        buffer: ImageBuffer,
        params: SortParams,
        x: int,
        y: int,
        w: int,
        h: int,
        mask: np.ndarray | None,
        refresh_callback,
    ):
        super().__init__("Pixel Sort")
        self._buffer = buffer
        self._params = params
        self._x = x
        self._y = y
        self._w = w
        self._h = h
        self._mask = mask.copy() if mask is not None else None
        self._refresh = refresh_callback

        # Snapshot only the affected region
        img = buffer.data
        if w > 0 and h > 0:
            self._old_region = img[y : y + h, x : x + w].copy()
        else:
            self._old_region = img.copy()

        self._new_region: np.ndarray | None = None

    def redo(self):
        if self._new_region is not None:
            # Re-apply cached result
            if self._w > 0 and self._h > 0:
                self._buffer.data[
                    self._y : self._y + self._h, self._x : self._x + self._w
                ] = self._new_region
            else:
                self._buffer.data[:] = self._new_region
        else:
            # First time: compute the sort
            result = sort_region(
                self._buffer.data,
                self._params,
                self._x,
                self._y,
                self._w,
                self._h,
                self._mask,
            )
            if self._w > 0 and self._h > 0:
                self._new_region = result[
                    self._y : self._y + self._h, self._x : self._x + self._w
                ].copy()
                self._buffer.data[
                    self._y : self._y + self._h, self._x : self._x + self._w
                ] = self._new_region
            else:
                self._new_region = result.copy()
                self._buffer.data[:] = self._new_region

        self._buffer.mark_modified()
        self._refresh()

    def undo(self):
        if self._w > 0 and self._h > 0:
            self._buffer.data[
                self._y : self._y + self._h, self._x : self._x + self._w
            ] = self._old_region
        else:
            self._buffer.data[:] = self._old_region

        self._buffer.mark_modified()
        self._refresh()


class SortWorker(QThread):
    """Background thread for live preview computation."""

    finished = Signal(object)  # np.ndarray or None

    def __init__(
        self,
        image_data: np.ndarray,
        params: SortParams,
        x: int,
        y: int,
        w: int,
        h: int,
        mask: np.ndarray | None,
    ):
        super().__init__()
        self._image = image_data.copy()
        self._params = params
        self._x = x
        self._y = y
        self._w = w
        self._h = h
        self._mask = mask.copy() if mask is not None else None

    def run(self):
        try:
            result = sort_region(
                self._image,
                self._params,
                self._x,
                self._y,
                self._w,
                self._h,
                self._mask,
            )
            self.finished.emit(result)
        except Exception:
            self.finished.emit(None)
