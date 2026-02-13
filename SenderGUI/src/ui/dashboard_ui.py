from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt

from components.waypointInput import WaypointInput
from components.waypointViewer import WaypointViewer
from components.missionViewer import MissionViewer
from components.mapViewer import MapViewer
from components.cameraFeed import CameraFeed
from components.cameraDiscovery import CameraDiscovery
from utility.udp_image_receiver import UDPImageReceiver

def circular_pixmap(pixmap, size):
    img = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
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

    def setup_ui(self, central_widget):
        self.main_layout = QVBoxLayout(central_widget)

        # --- Header with circular logo and title ---
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
        # --- End header ---

        # --- Main layout with left and right panels ---
        main_panel_layout = QHBoxLayout()

        self.left_panel = QVBoxLayout()
        self.right_panel = QVBoxLayout()

        self.input_panel = WaypointInput()
        self.camera_feed = CameraFeed()
        self.map_viewer = MapViewer()
        self.map_viewer.setMinimumSize(700, 500)
        self.map_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mission_control_viewer = MissionViewer()
        self.viewer_panel = WaypointViewer()

        # Start UDP image receiver for camera feed
        self.image_receiver = UDPImageReceiver(ip='127.0.0.1', port=5007)
        self.image_receiver.image_received.connect(self.camera_feed.update_image)
        self.image_receiver.start()
        print("[Dashboard] Camera feed receiver started on 127.0.0.1:5007")

        # Left panel: Mission Viewer -> Waypoint Viewer -> Map
        self.left_panel.addWidget(self.mission_control_viewer)
        self.left_panel.addWidget(self.viewer_panel)
        self.left_panel.addWidget(self.map_viewer)
        self.left_panel.addStretch()

        # Right panel: Waypoint Input -> Camera Feed
        self.right_panel.addWidget(self.input_panel)
        self.right_panel.addWidget(self.camera_feed)
        self.right_panel.addStretch()

        # Connections
        self.input_panel.submitted.connect(self.viewer_panel.add_waypoint)
        self.viewer_panel.mission_pushed.connect(self.mission_control_viewer.update_mission_viewer)
        self.viewer_panel.mission_pushed.connect(lambda _: self.map_viewer.set_destination_to_first_waypoint())
        self.map_viewer.refresh_map.clicked.connect(self.viewer_panel.get_all_mission_data)
        self.viewer_panel.waypoint_data.connect(self.map_viewer.update_map)

        # Left panel gets more space (stretch factor 7), right panel less (stretch factor 3)
        main_panel_layout.addLayout(self.left_panel, 7)
        main_panel_layout.addLayout(self.right_panel, 3)

        self.main_layout.addLayout(main_panel_layout)

    def on_gps_received(self, lat, lon):
        """Called when GPS data is received from ReceiverGUI"""
        if self.map_viewer:
            self.map_viewer.update_current_position(lat, lon)