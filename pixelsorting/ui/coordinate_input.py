from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class CoordinateInput(QDockWidget):
    coords_changed = Signal(int, int, int, int)  # x, y, w, h

    def __init__(self, parent=None):
        super().__init__("Selection", parent)
        self.setObjectName("coordinate_input")
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        self._block_signals = False
        self._build_ui()

    def _build_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        form = QFormLayout()

        self._spn_x = QSpinBox()
        self._spn_x.setRange(0, 99999)
        self._spn_x.valueChanged.connect(self._on_value_changed)
        form.addRow("X:", self._spn_x)

        self._spn_y = QSpinBox()
        self._spn_y.setRange(0, 99999)
        self._spn_y.valueChanged.connect(self._on_value_changed)
        form.addRow("Y:", self._spn_y)

        self._spn_w = QSpinBox()
        self._spn_w.setRange(0, 99999)
        self._spn_w.valueChanged.connect(self._on_value_changed)
        form.addRow("W:", self._spn_w)

        self._spn_h = QSpinBox()
        self._spn_h.setRange(0, 99999)
        self._spn_h.valueChanged.connect(self._on_value_changed)
        form.addRow("H:", self._spn_h)

        layout.addLayout(form)
        layout.addStretch()
        self.setWidget(container)

    def set_coords(self, x: int, y: int, w: int, h: int, block_signals: bool = False):
        if block_signals:
            self._block_signals = True
        try:
            self._spn_x.setValue(x)
            self._spn_y.setValue(y)
            self._spn_w.setValue(w)
            self._spn_h.setValue(h)
        finally:
            self._block_signals = False

    def get_coords(self) -> tuple:
        return (
            self._spn_x.value(),
            self._spn_y.value(),
            self._spn_w.value(),
            self._spn_h.value(),
        )

    def _on_value_changed(self):
        if not self._block_signals:
            self.coords_changed.emit(*self.get_coords())
