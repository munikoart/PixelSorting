from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from ..core.sort_params import IntervalMode, SortDirection, SortKey, SortParams


class SettingsPanel(QDockWidget):
    params_changed = Signal(object)  # SortParams
    apply_clicked = Signal()
    reset_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Sort Settings", parent)
        self.setObjectName("settings_panel")
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        self._block_signals = False
        self._build_ui()

    def _build_ui(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        form = QFormLayout()

        # Direction
        self._cmb_direction = QComboBox()
        self._cmb_direction.addItems(["Horizontal", "Vertical"])
        self._cmb_direction.currentIndexChanged.connect(self._emit_params)
        form.addRow("Direction:", self._cmb_direction)

        # Angle
        self._sld_angle = QSlider(Qt.Orientation.Horizontal)
        self._sld_angle.setRange(0, 360)
        self._sld_angle.setValue(0)
        self._spn_angle = QSpinBox()
        self._spn_angle.setRange(0, 360)
        self._spn_angle.setSuffix("°")
        self._spn_angle.setValue(0)
        self._sld_angle.valueChanged.connect(self._spn_angle.setValue)
        self._spn_angle.valueChanged.connect(self._sld_angle.setValue)
        self._spn_angle.valueChanged.connect(self._emit_params)
        angle_row = QHBoxLayout()
        angle_row.addWidget(self._sld_angle, 1)
        angle_row.addWidget(self._spn_angle)
        form.addRow("Angle:", angle_row)

        # Sort Key
        self._cmb_key = QComboBox()
        self._cmb_key.addItems(
            ["Brightness", "Hue", "Saturation", "Intensity", "Minimum", "Red", "Green", "Blue"]
        )
        self._cmb_key.currentIndexChanged.connect(self._emit_params)
        form.addRow("Sort Key:", self._cmb_key)

        # Interval Mode
        self._cmb_interval = QComboBox()
        self._cmb_interval.addItems(["Threshold", "Random", "Edges", "Waves", "None (full row)"])
        self._cmb_interval.currentIndexChanged.connect(self._emit_params)
        form.addRow("Interval:", self._cmb_interval)

        # Lower Threshold
        self._spn_lower = QDoubleSpinBox()
        self._spn_lower.setRange(0.0, 1.0)
        self._spn_lower.setSingleStep(0.01)
        self._spn_lower.setValue(0.25)
        self._spn_lower.setDecimals(2)
        self._spn_lower.valueChanged.connect(self._emit_params)
        form.addRow("Lower Threshold:", self._spn_lower)

        # Upper Threshold
        self._spn_upper = QDoubleSpinBox()
        self._spn_upper.setRange(0.0, 1.0)
        self._spn_upper.setSingleStep(0.01)
        self._spn_upper.setValue(0.80)
        self._spn_upper.setDecimals(2)
        self._spn_upper.valueChanged.connect(self._emit_params)
        form.addRow("Upper Threshold:", self._spn_upper)

        # Pixel Size
        self._spn_pixel_size = QSpinBox()
        self._spn_pixel_size.setRange(1, 32)
        self._spn_pixel_size.setValue(1)
        self._spn_pixel_size.valueChanged.connect(self._emit_params)
        form.addRow("Pixel Size:", self._spn_pixel_size)

        # Span Min
        self._spn_span_min = QSpinBox()
        self._spn_span_min.setRange(1, 10000)
        self._spn_span_min.setValue(1)
        self._spn_span_min.valueChanged.connect(self._emit_params)
        form.addRow("Span Min:", self._spn_span_min)

        # Span Max
        self._spn_span_max = QSpinBox()
        self._spn_span_max.setRange(0, 10000)
        self._spn_span_max.setValue(0)
        self._spn_span_max.setSpecialValueText("Unlimited")
        self._spn_span_max.valueChanged.connect(self._emit_params)
        form.addRow("Span Max:", self._spn_span_max)

        # Jitter
        self._sld_jitter = QSlider(Qt.Orientation.Horizontal)
        self._sld_jitter.setRange(0, 100)
        self._sld_jitter.setValue(0)
        self._lbl_jitter = QLabel("0")
        self._sld_jitter.valueChanged.connect(
            lambda v: self._lbl_jitter.setText(str(v))
        )
        self._sld_jitter.valueChanged.connect(self._emit_params)
        jitter_row = QHBoxLayout()
        jitter_row.addWidget(self._sld_jitter)
        jitter_row.addWidget(self._lbl_jitter)
        form.addRow("Jitter:", jitter_row)

        # Reverse
        self._chk_reverse = QCheckBox("Reverse sort order")
        self._chk_reverse.stateChanged.connect(self._emit_params)
        form.addRow("", self._chk_reverse)

        # Brush Size (for mask painting)
        self._spn_brush = QSpinBox()
        self._spn_brush.setRange(1, 200)
        self._spn_brush.setValue(20)
        self._spn_brush.setSuffix(" px")
        form.addRow("Brush Size:", self._spn_brush)

        # Eraser Size (for mask erasing)
        self._spn_eraser = QSpinBox()
        self._spn_eraser.setRange(1, 200)
        self._spn_eraser.setValue(20)
        self._spn_eraser.setSuffix(" px")
        form.addRow("Eraser Size:", self._spn_eraser)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self._btn_apply = QPushButton("Apply")
        self._btn_apply.setDefault(True)
        self._btn_apply.clicked.connect(self.apply_clicked.emit)
        btn_layout.addWidget(self._btn_apply)

        self._btn_reset = QPushButton("Reset")
        self._btn_reset.clicked.connect(self.reset_clicked.emit)
        btn_layout.addWidget(self._btn_reset)

        layout.addLayout(btn_layout)
        layout.addStretch()

        self.setWidget(container)

    def get_params(self) -> SortParams:
        direction_map = {0: SortDirection.HORIZONTAL, 1: SortDirection.VERTICAL}
        key_map = {
            0: SortKey.BRIGHTNESS,
            1: SortKey.HUE,
            2: SortKey.SATURATION,
            3: SortKey.INTENSITY,
            4: SortKey.MINIMUM,
            5: SortKey.RED,
            6: SortKey.GREEN,
            7: SortKey.BLUE,
        }
        interval_map = {
            0: IntervalMode.THRESHOLD,
            1: IntervalMode.RANDOM,
            2: IntervalMode.EDGES,
            3: IntervalMode.WAVES,
            4: IntervalMode.NONE,
        }

        return SortParams(
            direction=direction_map.get(self._cmb_direction.currentIndex(), SortDirection.HORIZONTAL),
            angle=float(self._spn_angle.value()),
            sort_key=key_map.get(self._cmb_key.currentIndex(), SortKey.BRIGHTNESS),
            interval_mode=interval_map.get(self._cmb_interval.currentIndex(), IntervalMode.THRESHOLD),
            lower_threshold=self._spn_lower.value(),
            upper_threshold=self._spn_upper.value(),
            pixel_size=self._spn_pixel_size.value(),
            span_min=self._spn_span_min.value(),
            span_max=self._spn_span_max.value(),
            jitter=self._sld_jitter.value(),
            reverse=self._chk_reverse.isChecked(),
        )

    def set_params(self, params: SortParams):
        self._block_signals = True
        try:
            self._cmb_direction.setCurrentIndex(
                0 if params.direction == SortDirection.HORIZONTAL else 1
            )
            self._spn_angle.setValue(int(params.angle))
            key_index = {
                SortKey.BRIGHTNESS: 0, SortKey.HUE: 1, SortKey.SATURATION: 2,
                SortKey.INTENSITY: 3, SortKey.MINIMUM: 4, SortKey.RED: 5,
                SortKey.GREEN: 6, SortKey.BLUE: 7,
            }
            self._cmb_key.setCurrentIndex(key_index.get(params.sort_key, 0))
            interval_index = {
                IntervalMode.THRESHOLD: 0, IntervalMode.RANDOM: 1,
                IntervalMode.EDGES: 2, IntervalMode.WAVES: 3, IntervalMode.NONE: 4,
            }
            self._cmb_interval.setCurrentIndex(interval_index.get(params.interval_mode, 0))
            self._spn_lower.setValue(params.lower_threshold)
            self._spn_upper.setValue(params.upper_threshold)
            self._spn_pixel_size.setValue(params.pixel_size)
            self._spn_span_min.setValue(params.span_min)
            self._spn_span_max.setValue(params.span_max)
            self._sld_jitter.setValue(params.jitter)
            self._chk_reverse.setChecked(params.reverse)
        finally:
            self._block_signals = False

    def _emit_params(self, *_args):
        if not self._block_signals:
            self.params_changed.emit(self.get_params())
