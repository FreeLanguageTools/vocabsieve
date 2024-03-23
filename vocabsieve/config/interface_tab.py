import platform
from PyQt5.QtWidgets import QFormLayout, QLabel, QColorDialog, QCheckBox, QComboBox, QPushButton, QSlider, QSpinBox, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt
import qdarktheme
from ..global_names import settings
from .base_tab import BaseTab
from ..models import FreqDisplayMode


class InterfaceTab(BaseTab):

    def initWidgets(self):
        self.allow_editing = QCheckBox(
            "Allow directly editing definition fields")
        self.primary = QCheckBox("*Use primary selection")
        self.freq_display_mode = QComboBox()

        self.theme = QComboBox()
        self.accent_color = QPushButton()
        self.accent_color.setText(settings.value("accent_color", "default"))
        self.accent_color.setToolTip("Hex color code (e.g. #ff0000 for red)")
        self.text_scale = QSlider(Qt.Horizontal)

        self.text_scale_label = QLabel("1.00x")
        self.text_scale_box = QWidget()

    def setupWidgets(self):
        self.freq_display_mode.addItems([
            FreqDisplayMode.stars,
            FreqDisplayMode.rank
        ])
        self.accent_color.clicked.connect(self.save_accent_color)
        self.text_scale.setTickPosition(QSlider.TicksBelow)
        self.text_scale.setTickInterval(10)
        self.text_scale.setSingleStep(5)
        self.text_scale.setValue(100)
        self.text_scale.setMinimum(50)
        self.text_scale.setMaximum(250)
        self.text_scale_box_layout = QHBoxLayout()
        self.text_scale_box.setLayout(self.text_scale_box_layout)
        self.text_scale_box_layout.addWidget(self.text_scale)
        self.text_scale_box_layout.addWidget(self.text_scale_label)
        self.theme.addItems(qdarktheme.get_themes())
        self.theme.addItem("system")

        self.minimum_main_window_width = QSpinBox()
        self.minimum_main_window_width.setMinimum(0)
        self.minimum_main_window_width.setMaximum(15360)
        self.minimum_main_window_width.setToolTip(
            "Set desired minimum window width of the main application - useful to make window snipping easier.")

        self.theme.currentTextChanged.connect(self.setupTheme)
        self.text_scale.valueChanged.connect(
            lambda _: self.text_scale_label.setText(format(self.text_scale.value() / 100, "1.2f") + "x")
        )

    def save_accent_color(self):
        color = QColorDialog.getColor()
        if color.isValid() and settings.value("theme") != "system":
            settings.setValue("accent_color", color.name())
            self.accent_color.setText(color.name())
            qdarktheme.setup_theme(
                settings.value("theme", "dark"),
                custom_colors={"primary": color.name()}
            )

    def setupTheme(self) -> None:
        theme = self.theme.currentText()  # auto, dark, light, system
        if theme == "system":
            return
        accent_color = self.accent_color.text()
        if accent_color == "default":  # default is not a color
            qdarktheme.setup_theme(
                theme=theme
            )
        else:
            qdarktheme.setup_theme(
                theme=theme,
                custom_colors={"primary": accent_color},
            )

    def setupLayout(self):
        layout = QFormLayout(self)
        layout.addRow(QLabel("<h3>Interface settings</h3>"))
        layout.addRow(QLabel("<h4>Settings marked * require a restart to take effect.</h4>"))
        if platform.system() == "Linux":
            # Primary selection is only available on Linux
            layout.addRow(self.primary)
        layout.addRow("Theme", self.theme)
        layout.addRow(QLabel('<i>◊ Changing to "system" requires a restart.</i>'))
        layout.addRow("*Minimum window width (Pixels)", self.minimum_main_window_width)
        layout.addRow("Accent color", self.accent_color)
        layout.addRow(self.allow_editing)
        layout.addRow(QLabel("Frequency display mode"), self.freq_display_mode)
        #layout.addRow(QLabel("*Interface layout orientation"), self.orientation)
        layout.addRow(QLabel("*Text scale"), self.text_scale_box)

    def setupAutosave(self):
        self.register_config_handler(self.freq_display_mode, "freq_display", "Stars (like Migaku)")
        self.register_config_handler(self.allow_editing, 'allow_editing', True)
        self.register_config_handler(self.primary, 'primary', False)
        self.register_config_handler(self.text_scale, 'text_scale', '100')
        self.register_config_handler(self.theme, 'theme', 'auto')
        self.register_config_handler(self.minimum_main_window_width, 'minimum_width', 550)
