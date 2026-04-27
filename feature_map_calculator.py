import sys
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QFrame, QScrollArea, QSizePolicy, QSpacerItem, QGroupBox,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QIntValidator


STYLE_SHEET = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget#central_widget {
    background-color: #1e1e2e;
}
QGroupBox {
    background-color: #2a2a3e;
    border: 1px solid #444466;
    border-radius: 8px;
    margin-top: 12px;
    padding: 8px;
    color: #cdd6f4;
    font-weight: bold;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #89b4fa;
}
QLabel {
    color: #cdd6f4;
    font-size: 13px;
}
QLabel#result_label {
    color: #a6e3a1;
    font-size: 22px;
    font-weight: bold;
}
QLabel#result_subtitle {
    color: #89b4fa;
    font-size: 12px;
}
QLabel#layer_title {
    color: #cba6f7;
    font-size: 12px;
    font-weight: bold;
}
QLineEdit {
    background-color: #313244;
    border: 1px solid #444466;
    border-radius: 6px;
    color: #cdd6f4;
    font-size: 13px;
    padding: 6px 10px;
    selection-background-color: #89b4fa;
}
QLineEdit:focus {
    border: 1px solid #89b4fa;
}
QComboBox {
    background-color: #313244;
    border: 1px solid #444466;
    border-radius: 6px;
    color: #cdd6f4;
    font-size: 13px;
    padding: 6px 10px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #89b4fa;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    border: 1px solid #444466;
    color: #cdd6f4;
    selection-background-color: #45475a;
}
QPushButton#add_btn {
    background-color: #313244;
    border: 1px dashed #89b4fa;
    border-radius: 6px;
    color: #89b4fa;
    font-size: 13px;
    padding: 8px;
}
QPushButton#add_btn:hover {
    background-color: #3d3d5c;
}
QPushButton#calc_btn {
    background-color: #89b4fa;
    border: none;
    border-radius: 8px;
    color: #1e1e2e;
    font-size: 15px;
    font-weight: bold;
    padding: 12px;
}
QPushButton#calc_btn:hover {
    background-color: #b4d0f7;
}
QPushButton#remove_btn {
    background-color: transparent;
    border: none;
    color: #f38ba8;
    font-size: 16px;
    font-weight: bold;
    padding: 0px 6px;
    max-width: 28px;
}
QPushButton#remove_btn:hover {
    color: #ff5555;
}
QFrame#result_frame {
    background-color: #2a2a3e;
    border: 1px solid #a6e3a1;
    border-radius: 10px;
}
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
"""


def calc_output_size(input_size: int, kernel: int, stride: int, padding: int) -> int:
    return math.floor((input_size + 2 * padding - kernel) / stride) + 1


class LayerRow(QFrame):
    def __init__(self, index: int, on_remove, parent=None):
        super().__init__(parent)
        self.index = index
        self.on_remove = on_remove
        self._build_ui()

    def _build_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame { background-color: #313244; border-radius: 8px; "
            "border: 1px solid #3d3d5c; margin: 2px 0; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 6, 8)
        layout.setSpacing(8)

        # Layer index label
        self.idx_label = QLabel(f"Layer {self.index}")
        self.idx_label.setObjectName("layer_title")
        self.idx_label.setFixedWidth(52)
        layout.addWidget(self.idx_label)

        # Layer type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Conv2D", "MaxPool2D", "AvgPool2D"])
        self.type_combo.setFixedWidth(110)
        layout.addWidget(self.type_combo)

        int_validator = QIntValidator(1, 9999)

        for label_text, width, placeholder in [
            ("Kernel", 60, "3"),
            ("Stride", 60, "1"),
            ("Padding", 65, "0"),
        ]:
            lbl = QLabel(label_text)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setStyleSheet("color: #a6adc8; font-size: 12px; background: transparent; border: none;")
            layout.addWidget(lbl)

            field = QLineEdit(placeholder)
            field.setValidator(int_validator)
            field.setFixedWidth(width)
            field.setAlignment(Qt.AlignCenter)
            layout.addWidget(field)

            attr = label_text.lower() + "_input"
            setattr(self, attr, field)

        layout.addStretch()

        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("remove_btn")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(lambda: self.on_remove(self))
        layout.addWidget(remove_btn)

    def update_index(self, new_index: int):
        self.index = new_index
        self.idx_label.setText(f"Layer {new_index}")

    def get_params(self):
        return {
            "type": self.type_combo.currentText(),
            "kernel": int(self.kernel_input.text() or 3),
            "stride": int(self.stride_input.text() or 1),
            "padding": int(self.padding_input.text() or 0),
        }


class ResultStepWidget(QFrame):
    def __init__(self, step: int, layer_type: str, in_w: int, in_h: int,
                 out_w: int, out_h: int, kernel: int, stride: int, padding: int,
                 parent=None):
        super().__init__(parent)
        self.setMinimumHeight(54)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(
            "QFrame { background-color: #2a2a3e; border-radius: 6px; border: 1px solid #3d3d5c; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        left = QVBoxLayout()
        title = QLabel(f"Layer {step}  —  {layer_type}")
        title.setStyleSheet("color: #cba6f7; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        params = QLabel(f"kernel={kernel}  stride={stride}  padding={padding}")
        params.setStyleSheet("color: #a6adc8; font-size: 11px; border: none; background: transparent;")
        left.addWidget(title)
        left.addWidget(params)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight)
        arrow = QLabel(f"{in_w} × {in_h}  →  {out_w} × {out_h}")
        arrow.setStyleSheet("color: #a6e3a1; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        arrow.setAlignment(Qt.AlignRight)
        right.addWidget(arrow)

        layout.addLayout(left, stretch=1)
        layout.addLayout(right)


class FeatureMapCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Feature Map Calculator")
        self.setMinimumSize(640, 560)
        self.resize(700, 680)
        self.setStyleSheet(STYLE_SHEET)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Title
        title_label = QLabel("Feature Map Size Calculator")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #89b4fa; font-size: 20px; font-weight: bold;")
        root.addWidget(title_label)

        formula_label = QLabel("Output = ⌊ (Input + 2·Padding − Kernel) / Stride ⌋ + 1")
        formula_label.setAlignment(Qt.AlignCenter)
        formula_label.setStyleSheet("color: #6c7086; font-size: 11px;")
        root.addWidget(formula_label)

        # Input image size
        img_group = QGroupBox("Input Image Size")
        img_layout = QHBoxLayout(img_group)
        img_layout.setSpacing(12)

        int_validator = QIntValidator(1, 99999)

        img_layout.addWidget(QLabel("Width:"))
        self.img_w_input = QLineEdit("224")
        self.img_w_input.setValidator(int_validator)
        self.img_w_input.setFixedWidth(90)
        self.img_w_input.setAlignment(Qt.AlignCenter)
        img_layout.addWidget(self.img_w_input)

        img_layout.addSpacing(20)
        img_layout.addWidget(QLabel("Height:"))
        self.img_h_input = QLineEdit("224")
        self.img_h_input.setValidator(int_validator)
        self.img_h_input.setFixedWidth(90)
        self.img_h_input.setAlignment(Qt.AlignCenter)
        img_layout.addWidget(self.img_h_input)

        img_layout.addStretch()
        root.addWidget(img_group)

        # Layers
        layers_group = QGroupBox("Layers")
        layers_outer = QVBoxLayout(layers_group)
        layers_outer.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(220)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.layers_layout = QVBoxLayout(scroll_content)
        self.layers_layout.setSpacing(6)
        self.layers_layout.setContentsMargins(2, 2, 2, 2)
        self.layers_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(scroll_content)
        layers_outer.addWidget(scroll)

        add_btn = QPushButton("+ Add Layer")
        add_btn.setObjectName("add_btn")
        add_btn.clicked.connect(self._add_layer)
        layers_outer.addWidget(add_btn)
        layers_outer.addStretch()  # pin scroll+button to top when GroupBox is tall

        root.addWidget(layers_group)

        # Calculate button
        calc_btn = QPushButton("Calculate")
        calc_btn.setObjectName("calc_btn")
        calc_btn.clicked.connect(self._calculate)
        root.addWidget(calc_btn)

        # Results area
        self.results_group = QGroupBox("Results")
        results_outer = QVBoxLayout(self.results_group)
        results_outer.setSpacing(8)
        results_outer.setContentsMargins(8, 8, 8, 8)

        # Scrollable step list
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setMinimumHeight(80)
        self.results_scroll.setMaximumHeight(260)

        steps_content = QWidget()
        steps_content.setStyleSheet("background: transparent;")
        self.results_steps_layout = QVBoxLayout(steps_content)
        self.results_steps_layout.setSpacing(6)
        self.results_steps_layout.setContentsMargins(2, 2, 2, 2)
        self.results_steps_layout.setAlignment(Qt.AlignTop)

        self.results_scroll.setWidget(steps_content)
        results_outer.addWidget(self.results_scroll)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #444466;")
        results_outer.addWidget(sep)

        # Final result — persistent, just update text each time
        self.final_frame = QFrame()
        self.final_frame.setObjectName("result_frame")
        final_layout = QVBoxLayout(self.final_frame)
        final_layout.setContentsMargins(16, 10, 16, 10)
        final_layout.setSpacing(4)

        self.result_subtitle = QLabel("Final Feature Map Size")
        self.result_subtitle.setObjectName("result_subtitle")
        self.result_subtitle.setAlignment(Qt.AlignCenter)
        final_layout.addWidget(self.result_subtitle)

        self.result_lbl = QLabel("")
        self.result_lbl.setObjectName("result_label")
        self.result_lbl.setAlignment(Qt.AlignCenter)
        final_layout.addWidget(self.result_lbl)

        results_outer.addWidget(self.final_frame)

        self.results_group.setVisible(False)
        root.addWidget(self.results_group)
        root.addStretch()  # absorb extra vertical space when window is tall

        self.layer_rows: list[LayerRow] = []
        self._add_layer()  # start with one default layer

    def _add_layer(self):
        index = len(self.layer_rows) + 1
        row = LayerRow(index, self._remove_layer)
        self.layers_layout.addWidget(row)
        self.layer_rows.append(row)

    def _remove_layer(self, row: LayerRow):
        if len(self.layer_rows) <= 1:
            return
        self.layers_layout.removeWidget(row)
        row.deleteLater()
        self.layer_rows.remove(row)
        for i, r in enumerate(self.layer_rows):
            r.update_index(i + 1)

    def _clear_results(self):
        while self.results_steps_layout.count() > 0:
            item = self.results_steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _calculate(self):
        try:
            in_w = int(self.img_w_input.text())
            in_h = int(self.img_h_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid image dimensions.")
            return

        if in_w <= 0 or in_h <= 0:
            QMessageBox.warning(self, "Input Error", "Image dimensions must be greater than 0.")
            return

        self._clear_results()

        cur_w, cur_h = in_w, in_h
        error_occurred = False

        for i, row in enumerate(self.layer_rows):
            params = row.get_params()
            k, s, p = params["kernel"], params["stride"], params["padding"]

            if s <= 0:
                QMessageBox.warning(self, "Input Error", f"Layer {i+1}: Stride must be >= 1.")
                error_occurred = True
                break

            out_w = calc_output_size(cur_w, k, s, p)
            out_h = calc_output_size(cur_h, k, s, p)

            if out_w <= 0 or out_h <= 0:
                QMessageBox.warning(
                    self, "Invalid Result",
                    f"Layer {i+1}: Output size became ≤ 0 ({out_w} × {out_h}).\n"
                    "Check kernel/stride/padding values."
                )
                error_occurred = True
                break

            step_widget = ResultStepWidget(
                i + 1, params["type"], cur_w, cur_h, out_w, out_h, k, s, p
            )
            self.results_steps_layout.addWidget(step_widget)
            cur_w, cur_h = out_w, out_h

        if not error_occurred:
            self.result_lbl.setText(f"{cur_w}  ×  {cur_h}")
            self.results_group.setVisible(True)
            # Defer scroll-to-bottom until after layout recalculation
            QApplication.processEvents()
            self.results_scroll.verticalScrollBar().setValue(
                self.results_scroll.verticalScrollBar().maximum()
            )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FeatureMapCalculator()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
