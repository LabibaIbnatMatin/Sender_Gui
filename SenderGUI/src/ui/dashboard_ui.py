from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QPushButton, QGroupBox, QSpinBox
)
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt

from components.waypointInput import WaypointInput
from components.waypointViewer import WaypointViewer
from components.missionViewer import MissionViewer
from components.mapViewer import MapViewer
from components.cameraFeed import CameraFeed
from components.cameraDiscovery import CameraDiscovery
from utility.udp_image_receiver import UDPImageReceiver
from utility.teensy_sender import TeensySender


def circular_pixmap(pixmap, size):
    img = pixmap.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )
    masked = QPixmap(size, size)
    masked.fill(Qt.GlobalColor.transparent)
    painter = QPainter(masked)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, img)
    painter.end()
    return masked


class DashboardUI:
    def __init__(self):
        self.map_viewer = None
        self.header = None
        self.right_panel = None
        self.left_panel = None
        self.viewer_panel = None
        self.mission_control_viewer = None
        self.input_panel = None
        self.camera_feed = None
        self.camera_discovery = None
        self.sidebar_layout = None
        self.main_layout = None
        self.image_receiver = None
        self.teensy = None

    def setup_ui(self, central_widget):
        self.main_layout = QVBoxLayout(central_widget)

        # Header
        header_outer_layout = QHBoxLayout()
        header_outer_layout.addStretch()
        header_inner_layout = QHBoxLayout()

        logo_label = QLabel()
        pixmap = QPixmap("/home/labiba-ibnat-matin/Downloads/mongol_barota.png")
        circle_size = 80
        circular = circular_pixmap(pixmap, circle_size)
        logo_label.setPixmap(circular)
        logo_label.setFixedSize(circle_size, circle_size)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title_label = QLabel("<b>Autonomous Dashboard</b>")
        title_label.setStyleSheet("""
            font-size: 40px;
            font-family: Arial, Helvetica, sans-serif;
            margin-left: 24px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        header_inner_layout.addWidget(logo_label)
        header_inner_layout.addWidget(title_label)
        header_outer_layout.addLayout(header_inner_layout)
        header_outer_layout.addStretch()
        self.main_layout.addLayout(header_outer_layout)

        # Main horizontal layout
        main_panel_layout = QHBoxLayout()
        self.right_panel = QVBoxLayout()
        self.left_panel = QVBoxLayout()

        # Create Teensy sender
        self.teensy = TeensySender()  # defaults can be changed via self.teensy.set_target(ip, port)

        # Antenna control group (left panel)
        antenna_group = QGroupBox("Antenna Control")
        ag_layout = QHBoxLayout()
        left_btn = QPushButton("Left")
        stop_btn = QPushButton("Stop")
        right_btn = QPushButton("Right")
        ag_layout.addWidget(left_btn)
        ag_layout.addWidget(stop_btn)
        ag_layout.addWidget(right_btn)

        # Speed control
        speed_label = QLabel("Speed")
        speed_spin = QSpinBox()
        speed_spin.setRange(0, 2000)
        speed_spin.setValue(1500)
        ag_layout.addWidget(speed_label)
        ag_layout.addWidget(speed_spin)

        antenna_group.setLayout(ag_layout)

        # Core widgets
        self.input_panel = WaypointInput()
        self.camera_feed = CameraFeed()
        self.map_viewer = MapViewer()
        self.map_viewer.setMinimumSize(700, 500)
        self.map_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mission_control_viewer = MissionViewer()
        self.viewer_panel = WaypointViewer()

        # Start UDP image receiver for camera feed
        self.image_receiver = UDPImageReceiver(ip='192.168.68.115', port=5007)
        self.image_receiver.image_received.connect(self.camera_feed.update_image)
        self.image_receiver.start()
        print("[Dashboard] Camera feed receiver started on 192.168.68.115:5007")

        # Left panel composition: antenna controls -> waypoint input -> camera feed
        self.left_panel.addWidget(antenna_group)
        self.left_panel.addWidget(self.input_panel)
        self.left_panel.addWidget(self.camera_feed)
        self.left_panel.addStretch()

        # Right panel composition: mission viewer -> waypoint viewer -> map
        self.right_panel.addWidget(self.mission_control_viewer)
        self.right_panel.addWidget(self.viewer_panel)
        self.right_panel.addWidget(self.map_viewer)
        self.right_panel.addStretch()

        # Connections between components
        self.input_panel.submitted.connect(self.viewer_panel.add_waypoint)
        self.viewer_panel.mission_pushed.connect(self.mission_control_viewer.update_mission_viewer)
        self.viewer_panel.mission_pushed.connect(lambda _: self.map_viewer.set_destination_to_latest_waypoint())
        self.map_viewer.refresh_map.clicked.connect(self.viewer_panel.get_all_mission_data)
        self.viewer_panel.waypoint_data.connect(self.map_viewer.update_map)

        # Antenna control signal wiring to Teensy
        left_btn.clicked.connect(lambda: self.teensy.send("LEFT"))
        right_btn.clicked.connect(lambda: self.teensy.send("RIGHT"))
        stop_btn.clicked.connect(lambda: self.teensy.send("STOP"))
        speed_spin.valueChanged.connect(lambda v: self.teensy.send_speed(v))

        # Add layouts with stretch factors
        main_panel_layout.addLayout(self.left_panel, 3)
        main_panel_layout.addLayout(self.right_panel, 7)
        self.main_layout.addLayout(main_panel_layout)

    def on_gps_received(self, lat, lon):
        if self.map_viewer:
            self.map_viewer.update_current_position(lat, lon)
