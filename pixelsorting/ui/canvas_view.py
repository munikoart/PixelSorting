import numpy as np
from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsView,
)

from .canvas_scene import CanvasScene


class SelectionRect(QGraphicsRectItem):
    """Visual selection rectangle overlay."""

    def __init__(self):
        super().__init__()
        pen = QPen(QColor(0, 120, 215), 1.5, Qt.PenStyle.DashLine)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(0, 120, 215, 40)))
        self.setZValue(10)


class CanvasView(QGraphicsView):
    """Graphics view with pan, zoom, selection, and mask painting."""

    # Signals
    selection_changed = Signal(int, int, int, int)  # x, y, w, h
    cursor_moved = Signal(int, int)  # image x, y
    zoom_changed = Signal(float)

    class Tool:
        SELECT = "select"
        PAN = "pan"
        PAINT = "paint"
        ERASE = "erase"

    def __init__(self, scene: CanvasScene, parent=None):
        super().__init__(scene, parent)
        self._scene = scene
        self._tool = self.Tool.SELECT
        self._zoom_level = 1.0

        # Selection state
        self._selecting = False
        self._sel_start = QPointF()
        self._selection_rect = SelectionRect()
        self._scene.addItem(self._selection_rect)
        self._selection_rect.setVisible(False)
        self._sel_x = 0
        self._sel_y = 0
        self._sel_w = 0
        self._sel_h = 0

        # Pan state
        self._panning = False
        self._pan_start = QPoint()

        # Mask painting state
        self._painting = False
        self._mask: np.ndarray | None = None
        self._brush_size = 20
        self._eraser_size = 20

        # View settings
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(QColor(42, 42, 42)))

    @property
    def tool(self):
        return self._tool

    @tool.setter
    def tool(self, value):
        self._tool = value
        if value == self.Tool.PAN:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif value == self.Tool.PAINT:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif value == self.Tool.ERASE:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    @property
    def selection(self) -> tuple:
        return (self._sel_x, self._sel_y, self._sel_w, self._sel_h)

    @property
    def mask(self) -> np.ndarray | None:
        return self._mask

    @property
    def brush_size(self) -> int:
        return self._brush_size

    @brush_size.setter
    def brush_size(self, value: int):
        self._brush_size = max(1, min(200, value))

    @property
    def eraser_size(self) -> int:
        return self._eraser_size

    @eraser_size.setter
    def eraser_size(self, value: int):
        self._eraser_size = max(1, min(200, value))

    def set_selection(self, x: int, y: int, w: int, h: int) -> None:
        """Set selection programmatically (from coordinate input)."""
        self._sel_x, self._sel_y = x, y
        self._sel_w, self._sel_h = w, h
        self._selection_rect.setRect(QRectF(x, y, w, h))
        self._selection_rect.setVisible(w > 0 and h > 0)
        self.viewport().update()

    def clear_selection(self) -> None:
        self._sel_x = self._sel_y = self._sel_w = self._sel_h = 0
        self._selection_rect.setVisible(False)
        self.selection_changed.emit(0, 0, 0, 0)

    def init_mask(self, width: int, height: int) -> None:
        self._mask = np.zeros((height, width), dtype=bool)

    def clear_mask(self) -> None:
        if self._mask is not None:
            self._mask.fill(False)
            self._scene.clear_mask_overlay()

    def fit_in_view(self) -> None:
        if self._scene.image_item:
            self.fitInView(self._scene.image_item, Qt.AspectRatioMode.KeepAspectRatio)
            self._zoom_level = self.transform().m11()
            self.zoom_changed.emit(self._zoom_level)

    def reset_zoom(self) -> None:
        self.resetTransform()
        self._zoom_level = 1.0
        self.zoom_changed.emit(self._zoom_level)

    def zoom_in(self) -> None:
        self._apply_zoom(1.25)

    def zoom_out(self) -> None:
        self._apply_zoom(0.8)

    def _apply_zoom(self, factor: float) -> None:
        new_zoom = self._zoom_level * factor
        if 0.01 < new_zoom < 100:
            self.scale(factor, factor)
            self._zoom_level = new_zoom
            self.zoom_changed.emit(self._zoom_level)

    # --- Events ---

    brush_size_changed = Signal(int)
    eraser_size_changed = Signal(int)

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Scroll wheel resizes brush when paint/erase tool is active
        if self._tool == self.Tool.PAINT:
            delta = event.angleDelta().y()
            step = max(1, self._brush_size // 5)
            if delta > 0:
                self.brush_size = self._brush_size + step
            elif delta < 0:
                self.brush_size = self._brush_size - step
            self.brush_size_changed.emit(self._brush_size)
            return

        if self._tool == self.Tool.ERASE:
            delta = event.angleDelta().y()
            step = max(1, self._eraser_size // 5)
            if delta > 0:
                self.eraser_size = self._eraser_size + step
            elif delta < 0:
                self.eraser_size = self._eraser_size - step
            self.eraser_size_changed.emit(self._eraser_size)
            return

        delta = event.angleDelta().y()
        if delta > 0:
            self._apply_zoom(1.15)
        elif delta < 0:
            self._apply_zoom(1.0 / 1.15)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Middle-click always pans
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        scene_pos = self.mapToScene(event.position().toPoint())

        if self._tool == self.Tool.SELECT:
            self._selecting = True
            self._sel_start = scene_pos
            self._selection_rect.setRect(QRectF(scene_pos, scene_pos))
            self._selection_rect.setVisible(True)

        elif self._tool == self.Tool.PAN:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        elif self._tool == self.Tool.PAINT:
            self._painting = True
            self._paint_at(scene_pos)

        elif self._tool == self.Tool.ERASE:
            self._painting = True
            self._erase_at(scene_pos)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        scene_pos = self.mapToScene(event.position().toPoint())

        # Emit cursor position
        ix, iy = int(scene_pos.x()), int(scene_pos.y())
        self.cursor_moved.emit(ix, iy)

        if self._panning:
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            return

        if self._selecting:
            rect = QRectF(self._sel_start, scene_pos).normalized()
            self._selection_rect.setRect(rect)
            self._update_selection_from_rect(rect)

        elif self._painting and self._tool == self.Tool.PAINT:
            self._paint_at(scene_pos)

        elif self._painting and self._tool == self.Tool.ERASE:
            self._erase_at(scene_pos)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(
                Qt.CursorShape.OpenHandCursor
                if self._tool == self.Tool.PAN
                else Qt.CursorShape.ArrowCursor
            )
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if self._selecting:
                self._selecting = False
                scene_pos = self.mapToScene(event.position().toPoint())
                rect = QRectF(self._sel_start, scene_pos).normalized()
                self._selection_rect.setRect(rect)
                self._update_selection_from_rect(rect)

            elif self._panning:
                self._panning = False
                self.setCursor(Qt.CursorShape.OpenHandCursor)

            elif self._painting:
                self._painting = False

        super().mouseReleaseEvent(event)

    def _update_selection_from_rect(self, rect: QRectF) -> None:
        r = rect.toAlignedRect()
        self._sel_x = max(0, r.x())
        self._sel_y = max(0, r.y())
        self._sel_w = r.width()
        self._sel_h = r.height()
        self.selection_changed.emit(self._sel_x, self._sel_y, self._sel_w, self._sel_h)

    def _paint_at(self, pos: QPointF) -> None:
        if self._mask is None:
            return
        ix, iy = int(pos.x()), int(pos.y())
        h, w = self._mask.shape
        r = self._brush_size // 2

        y0 = max(0, iy - r)
        y1 = min(h, iy + r + 1)
        x0 = max(0, ix - r)
        x1 = min(w, ix + r + 1)

        if y0 < y1 and x0 < x1:
            # Circular brush
            yy, xx = np.ogrid[y0 - iy : y1 - iy, x0 - ix : x1 - ix]
            circle = (xx * xx + yy * yy) <= r * r
            self._mask[y0:y1, x0:x1] |= circle
            self._update_mask_overlay()

    def _erase_at(self, pos: QPointF) -> None:
        if self._mask is None:
            return
        ix, iy = int(pos.x()), int(pos.y())
        h, w = self._mask.shape
        r = self._eraser_size // 2

        y0 = max(0, iy - r)
        y1 = min(h, iy + r + 1)
        x0 = max(0, ix - r)
        x1 = min(w, ix + r + 1)

        if y0 < y1 and x0 < x1:
            yy, xx = np.ogrid[y0 - iy : y1 - iy, x0 - ix : x1 - ix]
            circle = (xx * xx + yy * yy) <= r * r
            self._mask[y0:y1, x0:x1] &= ~circle
            self._update_mask_overlay()

    def _update_mask_overlay(self) -> None:
        """Render the mask as a semi-transparent red overlay on the canvas."""
        if self._mask is None or not np.any(self._mask):
            self._scene.clear_mask_overlay()
            return
        h, w = self._mask.shape
        overlay = np.zeros((h, w, 4), dtype=np.uint8)
        overlay[self._mask, 0] = 255  # Red channel
        overlay[self._mask, 3] = 80   # Alpha
        data = np.ascontiguousarray(overlay)
        qimg = QImage(data.data, w, h, w * 4, QImage.Format.Format_RGBA8888).copy()
        self._scene.set_mask_overlay(QPixmap.fromImage(qimg))
