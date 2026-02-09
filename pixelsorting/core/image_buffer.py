from pathlib import Path

import numpy as np
from PIL import Image


class ImageBuffer:
    """Numpy-backed image with file I/O and Qt conversion support."""

    def __init__(self):
        self._data: np.ndarray | None = None
        self._path: Path | None = None
        self._modified: bool = False

    @property
    def data(self) -> np.ndarray | None:
        return self._data

    @data.setter
    def data(self, value: np.ndarray):
        self._data = value
        self._modified = True

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def modified(self) -> bool:
        return self._modified

    @property
    def width(self) -> int:
        return self._data.shape[1] if self._data is not None else 0

    @property
    def height(self) -> int:
        return self._data.shape[0] if self._data is not None else 0

    @property
    def is_loaded(self) -> bool:
        return self._data is not None

    def load(self, path: str | Path) -> None:
        path = Path(path)
        img = Image.open(path).convert("RGB")
        self._data = np.array(img)
        self._path = path
        self._modified = False

    def save(self, path: str | Path | None = None) -> None:
        if self._data is None:
            raise ValueError("No image loaded")

        save_path = Path(path) if path else self._path
        if save_path is None:
            raise ValueError("No path specified")

        img = Image.fromarray(self._data)
        img.save(str(save_path))
        self._path = save_path
        self._modified = False

    def close(self) -> None:
        self._data = None
        self._path = None
        self._modified = False

    def to_qpixmap(self):
        """Convert to QPixmap for display."""
        from PySide6.QtGui import QImage, QPixmap

        if self._data is None:
            return QPixmap()

        h, w, c = self._data.shape
        bytes_per_line = w * c
        data = np.ascontiguousarray(self._data)

        if c == 3:
            fmt = QImage.Format.Format_RGB888
        elif c == 4:
            fmt = QImage.Format.Format_RGBA8888
        else:
            fmt = QImage.Format.Format_RGB888

        qimg = QImage(data.data, w, h, bytes_per_line, fmt)
        return QPixmap.fromImage(qimg.copy())

    def to_qimage(self):
        """Convert to QImage."""
        from PySide6.QtGui import QImage

        if self._data is None:
            return QImage()

        h, w, c = self._data.shape
        bytes_per_line = w * c
        data = np.ascontiguousarray(self._data)

        if c == 3:
            fmt = QImage.Format.Format_RGB888
        elif c == 4:
            fmt = QImage.Format.Format_RGBA8888
        else:
            fmt = QImage.Format.Format_RGB888

        return QImage(data.data, w, h, bytes_per_line, fmt).copy()

    def mark_saved(self) -> None:
        self._modified = False

    def mark_modified(self) -> None:
        self._modified = True
