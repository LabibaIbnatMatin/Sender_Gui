from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QComboBox, QPushButton, QLabel, QButtonGroup, QRadioButton, \
    QHBoxLayout
from PyQt6.QtCore import pyqtSignal

class WaypointInput(QWidget):
    submitted = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.header = QLabel("Waypoint Input")
        self.layout.addWidget(self.header)

        # Latitude Input
        self.latitude = QLineEdit()
        self.latitude.setPlaceholderText("Latitude")
        self.layout.addWidget(self.latitude)

        # Longitude Input
        self.longitude = QLineEdit()
        self.longitude.setPlaceholderText("Longitude")
        self.layout.addWidget(self.longitude)

        # Altitude Input
        self.altitude = QLineEdit()
        self.altitude.setPlaceholderText("Altitude (m)")
        self.layout.addWidget(self.altitude)

        # Select Control Mode
        self.control_group = QButtonGroup(self)
        self.radio_manual = QRadioButton("Manual")
        self.radio_autonomous = QRadioButton("Autonomous")
        self.radio_manual.setChecked(True)


        self.control_group.addButton(self.radio_manual)
        self.control_group.addButton(self.radio_autonomous)

        self.radio_button_layout = QHBoxLayout()
        self.radio_button_layout.addWidget(self.radio_manual)
        self.radio_button_layout.addWidget(self.radio_autonomous)
        self.layout.addLayout(self.radio_button_layout)

        # Type Select Dropdown
        self.waypoint_type = QComboBox()
        self.waypoint_type.addItem("GPS")
        self.waypoint_type.addItem("ArUco")
        self.waypoint_type.addItem("Object")
        self.layout.addWidget(self.waypoint_type)

        # Form Submission Button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.emit_data)
        self.layout.addWidget(self.submit_button)

        self.layout.addStretch()

    def emit_data(self):
        control = "Manual"
        if self.radio_autonomous.isChecked():
            control = "Autonomous"

        data = dict()
        data["control"] = control
        data["latitude"] = self.latitude.text()
        data["longitude"] = self.longitude.text()
        data["altitude"] = self.altitude.text()
        data["waypoint_type"] = self.waypoint_type.currentText()

        if self.radio_manual.isChecked():
            data["waypoint_type"] = "N/A"

        self.submitted.emit(data)