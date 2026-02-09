from PySide6.QtCore import QRectF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene


class CanvasScene(QGraphicsScene):
    """Scene managing image display and overlay layers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image_item: QGraphicsPixmapItem | None = None
        self._preview_item: QGraphicsPixmapItem | None = None
        self._mask_item: QGraphicsPixmapItem | None = None

    @property
    def image_item(self) -> QGraphicsPixmapItem | None:
        return self._image_item

    def set_image(self, pixmap: QPixmap) -> None:
        if self._image_item is not None:
            self.removeItem(self._image_item)
        self._image_item = self.addPixmap(pixmap)
        self._image_item.setZValue(0)
        self.setSceneRect(QRectF(pixmap.rect()))

    def update_image(self, pixmap: QPixmap) -> None:
        if self._image_item is not None:
            self._image_item.setPixmap(pixmap)
        else:
            self.set_image(pixmap)

    def set_preview(self, pixmap: QPixmap) -> None:
        if self._preview_item is not None:
            self._preview_item.setPixmap(pixmap)
        else:
            self._preview_item = self.addPixmap(pixmap)
            self._preview_item.setZValue(5)
            self._preview_item.setOpacity(0.85)

    def clear_preview(self) -> None:
        if self._preview_item is not None:
            self.removeItem(self._preview_item)
            self._preview_item = None

    def set_mask_overlay(self, pixmap: QPixmap) -> None:
        if self._mask_item is not None:
            self._mask_item.setPixmap(pixmap)
        else:
            self._mask_item = self.addPixmap(pixmap)
            self._mask_item.setZValue(2)

    def clear_mask_overlay(self) -> None:
        if self._mask_item is not None:
            self.removeItem(self._mask_item)
            self._mask_item = None

    def clear_all(self) -> None:
        self.clear_preview()
        self.clear_mask_overlay()
        if self._image_item is not None:
            self.removeItem(self._image_item)
            self._image_item = None
        self.setSceneRect(QRectF())
