from pathlib import Path

import numpy as np
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QUndoStack
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStatusBar,
    QToolBar,
)

from ..core.image_buffer import ImageBuffer
from ..core.sort_params import SortParams
from ..core.sorting_engine import sort_region
from .canvas_scene import CanvasScene
from .canvas_view import CanvasView
from .context_menu import ContextMenu
from .coordinate_input import CoordinateInput
from .settings_panel import SettingsPanel


IMAGE_FILTERS = "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;All Files (*)"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Sorting")
        self.setMinimumSize(900, 600)

        self._buffer = ImageBuffer()
        self._params = SortParams()
        self._undo_stack = QUndoStack(self)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(300)
        self._preview_timer.timeout.connect(self._run_preview)
        self._preview_enabled = False
        self._preview_worker = None

        self._setup_scene()
        self._setup_panels()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_shortcuts()
        self._setup_connections()
        self._restore_state()

        self.setAcceptDrops(True)

    # --- Setup ---

    def _setup_scene(self):
        self._scene = CanvasScene(self)
        self._view = CanvasView(self._scene, self)
        self.setCentralWidget(self._view)

    def _setup_panels(self):
        self._settings_panel = SettingsPanel(self)
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self._settings_panel
        )

        self._coord_input = CoordinateInput(self)
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self._coord_input
        )

        self._context_menu = ContextMenu(self)

    def _setup_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        self._act_open = QAction("&Open...", self)
        self._act_open.setShortcut(QKeySequence.StandardKey.Open)
        self._act_open.triggered.connect(self._open_file)
        file_menu.addAction(self._act_open)

        self._act_save = QAction("&Save", self)
        self._act_save.setShortcut(QKeySequence.StandardKey.Save)
        self._act_save.triggered.connect(self._save_file)
        file_menu.addAction(self._act_save)

        self._act_save_as = QAction("Save &As...", self)
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._act_save_as.triggered.connect(self._save_file_as)
        file_menu.addAction(self._act_save_as)

        file_menu.addSeparator()

        self._act_close = QAction("&Close Image", self)
        self._act_close.triggered.connect(self._close_image)
        file_menu.addAction(self._act_close)

        file_menu.addSeparator()

        self._act_exit = QAction("E&xit", self)
        self._act_exit.setShortcut(QKeySequence("Alt+F4"))
        self._act_exit.triggered.connect(self.close)
        file_menu.addAction(self._act_exit)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        self._act_undo = self._undo_stack.createUndoAction(self, "&Undo")
        self._act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(self._act_undo)

        self._act_redo = self._undo_stack.createRedoAction(self, "&Redo")
        self._act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(self._act_redo)

        edit_menu.addSeparator()

        self._act_select_all = QAction("Select &All", self)
        self._act_select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self._act_select_all.triggered.connect(self._select_all)
        edit_menu.addAction(self._act_select_all)

        self._act_clear_sel = QAction("&Clear Selection", self)
        self._act_clear_sel.setShortcut(QKeySequence("Escape"))
        self._act_clear_sel.triggered.connect(self._view.clear_selection)
        edit_menu.addAction(self._act_clear_sel)

        # View menu
        view_menu = menubar.addMenu("&View")

        self._act_fit = QAction("&Fit to Window", self)
        self._act_fit.setShortcut(QKeySequence("Ctrl+0"))
        self._act_fit.triggered.connect(self._view.fit_in_view)
        view_menu.addAction(self._act_fit)

        self._act_reset_zoom = QAction("&Reset Zoom (100%)", self)
        self._act_reset_zoom.setShortcut(QKeySequence("Ctrl+1"))
        self._act_reset_zoom.triggered.connect(self._view.reset_zoom)
        view_menu.addAction(self._act_reset_zoom)

        self._act_zoom_in = QAction("Zoom &In", self)
        self._act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self._act_zoom_in.triggered.connect(self._view.zoom_in)
        view_menu.addAction(self._act_zoom_in)

        self._act_zoom_out = QAction("Zoom &Out", self)
        self._act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self._act_zoom_out.triggered.connect(self._view.zoom_out)
        view_menu.addAction(self._act_zoom_out)

        view_menu.addSeparator()
        view_menu.addAction(self._settings_panel.toggleViewAction())
        view_menu.addAction(self._coord_input.toggleViewAction())

        # Sort menu
        sort_menu = menubar.addMenu("&Sort")

        self._act_apply = QAction("&Apply Sort", self)
        self._act_apply.setShortcut(QKeySequence("Ctrl+Return"))
        self._act_apply.triggered.connect(self._apply_sort)
        sort_menu.addAction(self._act_apply)

        self._act_preview_toggle = QAction("&Live Preview", self)
        self._act_preview_toggle.setCheckable(True)
        self._act_preview_toggle.setShortcut(QKeySequence("Ctrl+P"))
        self._act_preview_toggle.toggled.connect(self._toggle_preview)
        sort_menu.addAction(self._act_preview_toggle)

        sort_menu.addSeparator()

        self._act_reset_params = QAction("&Reset Parameters", self)
        self._act_reset_params.triggered.connect(self._reset_params)
        sort_menu.addAction(self._act_reset_params)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        self._act_tool_select = QAction("&Select Tool", self)
        self._act_tool_select.setShortcut(QKeySequence("S"))
        self._act_tool_select.triggered.connect(
            lambda: setattr(self._view, "tool", CanvasView.Tool.SELECT)
        )
        tools_menu.addAction(self._act_tool_select)

        self._act_tool_pan = QAction("&Pan Tool", self)
        self._act_tool_pan.setShortcut(QKeySequence("H"))
        self._act_tool_pan.triggered.connect(
            lambda: setattr(self._view, "tool", CanvasView.Tool.PAN)
        )
        tools_menu.addAction(self._act_tool_pan)

        self._act_tool_paint = QAction("&Paint Mask Tool", self)
        self._act_tool_paint.setShortcut(QKeySequence("B"))
        self._act_tool_paint.triggered.connect(self._activate_paint_tool)
        tools_menu.addAction(self._act_tool_paint)

        self._act_tool_erase = QAction("&Erase Mask Tool", self)
        self._act_tool_erase.setShortcut(QKeySequence("E"))
        self._act_tool_erase.triggered.connect(self._activate_erase_tool)
        tools_menu.addAction(self._act_tool_erase)

        self._act_clear_mask = QAction("&Clear Mask", self)
        self._act_clear_mask.triggered.connect(self._view.clear_mask)
        tools_menu.addAction(self._act_clear_mask)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setObjectName("main_toolbar")
        self.addToolBar(toolbar)

        toolbar.addAction(self._act_open)
        toolbar.addAction(self._act_save)
        toolbar.addSeparator()
        toolbar.addAction(self._act_undo)
        toolbar.addAction(self._act_redo)
        toolbar.addSeparator()
        toolbar.addAction(self._act_tool_select)
        toolbar.addAction(self._act_tool_pan)
        toolbar.addAction(self._act_tool_paint)
        toolbar.addAction(self._act_tool_erase)
        toolbar.addSeparator()
        toolbar.addAction(self._act_apply)
        toolbar.addAction(self._act_preview_toggle)

    def _setup_statusbar(self):
        self._statusbar = QStatusBar(self)
        self.setStatusBar(self._statusbar)

        self._lbl_coords = QLabel("X: — Y: —")
        self._lbl_zoom = QLabel("100%")
        self._lbl_dims = QLabel("")

        self._statusbar.addWidget(self._lbl_coords)
        self._statusbar.addPermanentWidget(self._lbl_dims)
        self._statusbar.addPermanentWidget(self._lbl_zoom)

    def _setup_shortcuts(self):
        pass  # Shortcuts already assigned to actions

    def _setup_connections(self):
        self._view.selection_changed.connect(self._on_selection_changed)
        self._view.cursor_moved.connect(self._on_cursor_moved)
        self._view.zoom_changed.connect(self._on_zoom_changed)

        self._coord_input.coords_changed.connect(self._on_coords_input_changed)

        self._settings_panel.params_changed.connect(self._on_params_changed)
        self._settings_panel.apply_clicked.connect(self._apply_sort)
        self._settings_panel.reset_clicked.connect(self._reset_params)

        # Brush size: spinbox <-> canvas view (bidirectional)
        self._settings_panel._spn_brush.valueChanged.connect(
            lambda v: setattr(self._view, "brush_size", v)
        )
        self._view.brush_size_changed.connect(self._settings_panel._spn_brush.setValue)

        # Eraser size: spinbox <-> canvas view (bidirectional)
        self._settings_panel._spn_eraser.valueChanged.connect(
            lambda v: setattr(self._view, "eraser_size", v)
        )
        self._view.eraser_size_changed.connect(self._settings_panel._spn_eraser.setValue)

    # --- File Operations ---

    def _open_file(self):
        if not self._check_unsaved():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", IMAGE_FILTERS)
        if path:
            self._load_image(path)

    def _load_image(self, path: str):
        try:
            self._buffer.load(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open image:\n{e}")
            return

        self._refresh_canvas()
        self._view.fit_in_view()
        self._view.init_mask(self._buffer.width, self._buffer.height)
        self._undo_stack.clear()
        self._update_title()
        self._lbl_dims.setText(f"{self._buffer.width} x {self._buffer.height}")

    def _commit_preview_if_active(self):
        """If live preview is showing, apply the sort so the buffer matches what's on screen."""
        if self._preview_enabled and self._scene._preview_item is not None:
            self._apply_sort()
            self._scene.clear_preview()

    def _save_file(self):
        if not self._buffer.is_loaded:
            return
        self._commit_preview_if_active()
        if self._buffer.path is None:
            self._save_file_as()
            return
        try:
            self._buffer.save()
            self._update_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def _save_file_as(self):
        if not self._buffer.is_loaded:
            return
        self._commit_preview_if_active()
        path, _ = QFileDialog.getSaveFileName(self, "Save Image As", "", IMAGE_FILTERS)
        if path:
            try:
                self._buffer.save(path)
                self._update_title()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def _close_image(self):
        if not self._check_unsaved():
            return
        self._buffer.close()
        self._scene.clear_all()
        self._view.clear_selection()
        self._undo_stack.clear()
        self._update_title()
        self._lbl_dims.setText("")

    # --- Canvas ---

    def _refresh_canvas(self):
        if self._buffer.is_loaded:
            pixmap = self._buffer.to_qpixmap()
            self._scene.update_image(pixmap)

    # --- Selection ---

    def _on_selection_changed(self, x, y, w, h):
        self._coord_input.set_coords(x, y, w, h, block_signals=True)
        if self._preview_enabled:
            self._preview_timer.start()

    def _on_coords_input_changed(self, x, y, w, h):
        self._view.set_selection(x, y, w, h)
        if self._preview_enabled:
            self._preview_timer.start()

    def _select_all(self):
        if self._buffer.is_loaded:
            self._view.set_selection(0, 0, self._buffer.width, self._buffer.height)
            self._coord_input.set_coords(
                0, 0, self._buffer.width, self._buffer.height, block_signals=True
            )

    # --- Cursor / Zoom ---

    def _on_cursor_moved(self, x, y):
        self._lbl_coords.setText(f"X: {x}  Y: {y}")

    def _on_zoom_changed(self, zoom):
        self._lbl_zoom.setText(f"{zoom * 100:.0f}%")

    # --- Sorting ---

    def _on_params_changed(self, params: SortParams):
        self._params = params
        if self._preview_enabled:
            self._preview_timer.start()

    def _apply_sort(self):
        if not self._buffer.is_loaded:
            return

        x, y, w, h = self._view.selection

        # Only pass mask if the user actually painted something
        mask = self._view.mask
        if mask is not None and not np.any(mask):
            mask = None

        # Crop mask to selection bounds when selection is active
        if mask is not None and w > 0 and h > 0:
            mask = mask[y : y + h, x : x + w].copy()

        from ..commands.sort_command import SortCommand

        cmd = SortCommand(
            self._buffer, self._params.copy(), x, y, w, h, mask, self._refresh_canvas
        )
        self._undo_stack.push(cmd)
        self._scene.clear_preview()
        self._update_title()

    def _toggle_preview(self, enabled):
        self._preview_enabled = enabled
        if enabled:
            self._preview_timer.start()
        else:
            self._preview_timer.stop()
            self._scene.clear_preview()

    def _run_preview(self):
        if not self._buffer.is_loaded or not self._preview_enabled:
            return

        from ..commands.sort_command import SortWorker

        x, y, w, h = self._view.selection

        # Only pass mask if the user actually painted something
        mask = self._view.mask
        if mask is not None and not np.any(mask):
            mask = None

        # Crop mask to selection bounds when selection is active
        if mask is not None and w > 0 and h > 0:
            mask = mask[y : y + h, x : x + w].copy()

        # Run in background thread
        if self._preview_worker is not None and self._preview_worker.isRunning():
            return  # Skip if previous preview still running

        self._preview_worker = SortWorker(
            self._buffer.data, self._params.copy(), x, y, w, h, mask
        )
        self._preview_worker.finished.connect(self._on_preview_done)
        self._preview_worker.start()

    def _on_preview_done(self, result):
        if result is not None and self._preview_enabled:
            from PySide6.QtGui import QImage, QPixmap
            import numpy as np

            h, w, c = result.shape
            bpl = w * c
            data = np.ascontiguousarray(result)
            fmt = QImage.Format.Format_RGB888 if c == 3 else QImage.Format.Format_RGBA8888
            qimg = QImage(data.data, w, h, bpl, fmt).copy()
            self._scene.set_preview(QPixmap.fromImage(qimg))

    def _reset_params(self):
        self._params = SortParams()
        self._settings_panel.set_params(self._params)

    # --- Paint tool ---

    def _activate_paint_tool(self):
        if self._buffer.is_loaded and self._view.mask is None:
            self._view.init_mask(self._buffer.width, self._buffer.height)
        self._view.tool = CanvasView.Tool.PAINT

    def _activate_erase_tool(self):
        if self._buffer.is_loaded and self._view.mask is None:
            self._view.init_mask(self._buffer.width, self._buffer.height)
        self._view.tool = CanvasView.Tool.ERASE

    # --- Context menu ---

    def contextMenuEvent(self, event):
        if self._buffer.is_loaded:
            self._context_menu.show_at(
                event.globalPos(), self._params, self._apply_sort
            )

    # --- Window management ---

    def _update_title(self):
        title = "Pixel Sorting"
        if self._buffer.path:
            title = f"{self._buffer.path.name} — {title}"
        if self._buffer.modified:
            title = f"* {title}"
        self.setWindowTitle(title)

    def _check_unsaved(self) -> bool:
        """Returns True if it's OK to proceed (discard/save), False to cancel."""
        if not self._buffer.modified:
            return True
        reply = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "The image has been modified. Do you want to save your changes?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if reply == QMessageBox.StandardButton.Save:
            self._save_file()
            return True
        if reply == QMessageBox.StandardButton.Discard:
            return True
        return False  # Cancel

    def closeEvent(self, event):
        if not self._check_unsaved():
            event.ignore()
            return
        self._save_state()
        event.accept()

    def _save_state(self):
        settings = QSettings("PixelSorting", "PixelSorting")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def _restore_state(self):
        settings = QSettings("PixelSorting", "PixelSorting")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    # --- Drag and drop ---

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    ext = Path(url.toLocalFile()).suffix.lower()
                    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"):
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dropEvent(self, event):
        if not self._check_unsaved():
            return
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self._load_image(url.toLocalFile())
                break
