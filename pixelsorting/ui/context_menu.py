from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu, QWidget

from ..core.sort_params import IntervalMode, SortDirection, SortKey, SortParams


class ContextMenu:
    def __init__(self, parent: QWidget):
        self._parent = parent

    def show_at(self, pos: QPoint, params: SortParams, apply_callback):
        menu = QMenu(self._parent)

        # Quick direction toggle
        dir_menu = menu.addMenu("Direction")
        for d in SortDirection:
            action = dir_menu.addAction(d.value.capitalize())
            action.setCheckable(True)
            action.setChecked(params.direction == d)
            action.triggered.connect(
                lambda checked, dd=d: self._set_and_apply(
                    params, "direction", dd, apply_callback
                )
            )

        # Quick sort key
        key_menu = menu.addMenu("Sort Key")
        for k in SortKey:
            action = key_menu.addAction(k.value.capitalize())
            action.setCheckable(True)
            action.setChecked(params.sort_key == k)
            action.triggered.connect(
                lambda checked, kk=k: self._set_and_apply(
                    params, "sort_key", kk, apply_callback
                )
            )

        # Quick interval mode
        interval_menu = menu.addMenu("Interval")
        for m in IntervalMode:
            action = interval_menu.addAction(m.value.capitalize())
            action.setCheckable(True)
            action.setChecked(params.interval_mode == m)
            action.triggered.connect(
                lambda checked, mm=m: self._set_and_apply(
                    params, "interval_mode", mm, apply_callback
                )
            )

        menu.addSeparator()

        # Reverse toggle
        reverse_action = menu.addAction("Reverse")
        reverse_action.setCheckable(True)
        reverse_action.setChecked(params.reverse)
        reverse_action.triggered.connect(
            lambda checked: self._set_and_apply(
                params, "reverse", checked, apply_callback
            )
        )

        menu.addSeparator()

        # Apply
        apply_action = menu.addAction("Apply Sort")
        apply_action.triggered.connect(apply_callback)

        menu.exec(pos)

    def _set_and_apply(self, params, attr, value, callback):
        setattr(params, attr, value)
        # Update the settings panel
        main_window = self._parent
        if hasattr(main_window, "_settings_panel"):
            main_window._settings_panel.set_params(params)
        callback()
