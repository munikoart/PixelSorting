import sys

from PySide6.QtWidgets import QApplication

from pixelsorting.ui.main_window import MainWindow

PASTEL_PINK_STYLE = """
QMainWindow, QWidget {
    background-color: #FFE4EC;
    color: #5C3A4A;
}
QMenuBar {
    background-color: #FFD1DC;
    color: #5C3A4A;
    border-bottom: 1px solid #F4B8C8;
}
QMenuBar::item:selected {
    background-color: #FFB6C8;
}
QMenu {
    background-color: #FFF0F3;
    color: #5C3A4A;
    border: 1px solid #F4B8C8;
}
QMenu::item:selected {
    background-color: #FFD1DC;
}
QToolBar {
    background-color: #FFD1DC;
    border-bottom: 1px solid #F4B8C8;
    spacing: 4px;
    padding: 2px;
}
QToolButton {
    background-color: transparent;
    color: #5C3A4A;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px;
}
QToolButton:hover {
    background-color: #FFB6C8;
    border-color: #F4A0B8;
}
QToolButton:checked {
    background-color: #FFB6C8;
}
QDockWidget {
    color: #5C3A4A;
    titlebar-close-icon: none;
}
QDockWidget::title {
    background-color: #FFD1DC;
    padding: 6px;
    border: 1px solid #F4B8C8;
}
QStatusBar {
    background-color: #FFD1DC;
    color: #5C3A4A;
    border-top: 1px solid #F4B8C8;
}
QPushButton {
    background-color: #FFB6C8;
    color: #5C3A4A;
    border: 1px solid #F4A0B8;
    border-radius: 5px;
    padding: 5px 14px;
}
QPushButton:hover {
    background-color: #FFA4BC;
}
QPushButton:pressed {
    background-color: #FF8FAD;
}
QComboBox {
    background-color: #FFF0F3;
    color: #5C3A4A;
    border: 1px solid #F4B8C8;
    border-radius: 4px;
    padding: 3px 6px;
}
QComboBox:hover {
    border-color: #F4A0B8;
}
QComboBox::drop-down {
    border-left: 1px solid #F4B8C8;
    background-color: #FFD1DC;
}
QComboBox QAbstractItemView {
    background-color: #FFF0F3;
    color: #5C3A4A;
    selection-background-color: #FFD1DC;
}
QSpinBox, QDoubleSpinBox {
    background-color: #FFF0F3;
    color: #5C3A4A;
    border: 1px solid #F4B8C8;
    border-radius: 4px;
    padding: 2px 4px;
}
QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #F4A0B8;
}
QSlider::groove:horizontal {
    background-color: #F4B8C8;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background-color: #FF8FAD;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    border: 1px solid #E8779A;
}
QSlider::handle:horizontal:hover {
    background-color: #FF7BA0;
}
QCheckBox {
    color: #5C3A4A;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #F4A0B8;
    border-radius: 3px;
    background-color: #FFF0F3;
}
QCheckBox::indicator:checked {
    background-color: #FF8FAD;
    border-color: #E8779A;
}
QLabel {
    color: #5C3A4A;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background-color: #FFE4EC;
    border: none;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #F4B8C8;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background-color: #FF8FAD;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0; width: 0;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pixel Sorting")
    app.setOrganizationName("PixelSorting")
    app.setStyleSheet(PASTEL_PINK_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
