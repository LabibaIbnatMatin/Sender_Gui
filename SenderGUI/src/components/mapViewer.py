from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPointF, QPropertyAnimation, QEasingCurve, QObject, pyqtProperty
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QHBoxLayout

from components.mapModal import MapModal
from utility.static_mapping import MappingUtility

from math import radians, cos, sin, sqrt, atan2

class AnimatedMarker(QObject):
    position_changed = pyqtSignal()
    def __init__(self, lat, lon):
        super().__init__()
        self._lat = lat
        self._lon = lon
    @pyqtProperty(float)
    def lat(self):
        return self._lat
    @lat.setter
    def lat(self, value):
        self._lat = value
        self.position_changed.emit()
    @pyqtProperty(float)
    def lon(self):
        return self._lon
    @lon.setter
    def lon(self, value):
        self._lon = value
        self.position_changed.emit()
    def animate_to(self, target_lat, target_lon, duration=800):
        self.lat_anim = QPropertyAnimation(self, b"lat")
        self.lat_anim.setDuration(duration)
        self.lat_anim.setStartValue(self._lat)
        self.lat_anim.setEndValue(target_lat)
        self.lat_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.lon_anim = QPropertyAnimation(self, b"lon")
        self.lon_anim.setDuration(duration)
        self.lon_anim.setStartValue(self._lon)
        self.lon_anim.setEndValue(target_lon)
        self.lon_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.lat_anim.start()
        self.lon_anim.start()

class MapViewer(QWidget):
    waypoint_data = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.gps_status = QLabel("GPS:  Waiting for data... | Zoom: 15")
        self.gps_status.setStyleSheet("color: orange; font-weight: bold; padding: 5px;")
        self.main_layout.addWidget(self.gps_status)
        self.map_label = QLabel("")
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_lat = 22.80978657890875
        self.current_lon = 90.41065979003906
        self.current_zoom = 15
        self.destination_lat = None
        self.destination_lon = None
        self.gps_connected = False
        self.gps_path = []
        self.max_path_points = 100
        self.show_path = True
        self.animated_marker = AnimatedMarker(self.current_lat, self.current_lon)
        self.animated_marker.position_changed.connect(self.redraw_markers)
        self.waypoints = []
        self.mapping_utility = MappingUtility(self.current_lat, self.current_lon, self.current_zoom)
        self.map_path = self.mapping_utility.get_map_path()
        self.base_pixmap = QPixmap(self.map_path)
        self.map_label.setPixmap(self.base_pixmap)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.map_label)
        self.main_layout.addWidget(self.scroll_area)
        button_layout = QHBoxLayout()
        self.refresh_map = QPushButton("Refresh Waypoints")
        button_layout.addWidget(self.refresh_map)
        self.toggle_path_btn = QPushButton("Hide Path")
        self.toggle_path_btn.clicked.connect(self.toggle_path_visibility)
        button_layout.addWidget(self.toggle_path_btn)
        self.clear_path_btn = QPushButton(" Clear Path")
        self.clear_path_btn.clicked.connect(self.clear_path)
        button_layout.addWidget(self.clear_path_btn)
        self.map_button = QPushButton("View Enlarged Map")
        self.map_button.clicked.connect(self.show_enlarged_map)
        button_layout.addWidget(self.map_button)
        self.main_layout.addLayout(button_layout)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.redraw_markers)
        self.update_timer.start(50)

    def set_destination_to_latest_waypoint(self):
        """Set the destination to the latest waypoint (if any)"""
        if self.waypoints:
            last_wp = self.waypoints[-1]
            lat = last_wp.get('latitude') if isinstance(last_wp, dict) else getattr(last_wp, 'latitude', None)
            lon = last_wp.get('longitude') if isinstance(last_wp, dict) else getattr(last_wp, 'longitude', None)
            try:
                self.destination_lat = float(lat)
                self.destination_lon = float(lon)
            except Exception:
                self.destination_lat = None
                self.destination_lon = None
        else:
            self.destination_lat = None
            self.destination_lon = None
        self.redraw_markers()

    def update_map(self, coords):
        """Update waypoint markers (red) - these stay fixed on map"""
        print(f"MapViewer: Updating {len(coords)} waypoint markers")
        self.waypoints = coords
        self.mapping_utility.add_markers(coords)
        self.map_path = self.mapping_utility.get_map_path()
        self.base_pixmap = QPixmap(self.map_path)
        self.set_destination_to_latest_waypoint()  # Always set latest as destination

    def update_current_position(self, lat, lon):
        """Update GPS position from ReceiverGUI (smooth animated blue marker)"""
        print(f"MapViewer: GPS updated to Lat={lat}, Lon={lon}")
        if not self.gps_connected:
            self.gps_connected = True
            print("GPS Connected!")
        self.gps_path.append((lat, lon))
        if len(self.gps_path) > self.max_path_points:
            self.gps_path.pop(0)
        self.current_lat = lat
        self.current_lon = lon
        self.animated_marker.animate_to(lat, lon, duration=800)
        self.mapping_utility.update_position(lat, lon)
        self.update_gps_status()
        # --- Check if destination is reached ---
        if self.destination_lat is not None and self.destination_lon is not None:
            if self.is_at_destination(lat, lon, self.destination_lat, self.destination_lon):
                print("Destination reached! Clearing waypoints.")
                self.waypoints.clear()
                self.destination_lat = None
                self.destination_lon = None
                self.mapping_utility.add_markers([])  # Remove markers from map
                self.map_path = self.mapping_utility.get_map_path()
                self.base_pixmap = QPixmap(self.map_path)
                self.redraw_markers()

    def is_at_destination(self, lat1, lon1, lat2, lon2, threshold=5):
        """Check if current position is within threshold (meters) of destination"""
        # Haversine formula
        R = 6371000  # Earth radius in meters
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        return distance <= threshold

    def toggle_path_visibility(self):
        self.show_path = not self.show_path
        if self.show_path:
            self.toggle_path_btn.setText(" Hide Path")
        else:
            self.toggle_path_btn.setText("Show Path")
        self.redraw_markers()

    def clear_path(self):
        self.gps_path.clear()
        print("GPS path cleared")
        self.redraw_markers()

    def redraw_markers(self):
        if self.base_pixmap.isNull():
            return
        pixmap = self.base_pixmap.copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        map_width = pixmap.width()
        map_height = pixmap.height()
        # Draw GPS path trail (blue line)
        if self.show_path and len(self.gps_path) > 1:
            pen = QPen(QColor(66, 133, 244, 180))
            pen.setWidth(4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            points = []
            for lat, lon in self.gps_path:
                x, y = self.lat_lon_to_pixel(lat, lon, map_width, map_height)
                if x is not None and y is not None:
                    points.append(QPointF(x, y))
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        # Draw animated blue current position marker (Google Maps style)
        current_x, current_y = self.lat_lon_to_pixel(
            self.animated_marker.lat,
            self.animated_marker.lon,
            map_width,
            map_height
        )
        # Draw line from current position to destination (if both exist)
        if (
            self.destination_lat is not None and self.destination_lon is not None
            and self.animated_marker.lat is not None and self.animated_marker.lon is not None
        ):
            dest_x, dest_y = self.lat_lon_to_pixel(self.destination_lat, self.destination_lon, map_width, map_height)
            curr_x, curr_y = self.lat_lon_to_pixel(self.animated_marker.lat, self.animated_marker.lon, map_width, map_height)
            if dest_x is not None and dest_y is not None and curr_x is not None and curr_y is not None:
                pen = QPen(QColor(234, 67, 53, 200))  # Red for destination line
                pen.setWidth(4)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(QPointF(curr_x, curr_y), QPointF(dest_x, dest_y))
                # Draw destination marker (red)
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                painter.setBrush(QColor(234, 67, 53))  # Google red
                painter.drawEllipse(QPointF(dest_x, dest_y), 12, 12)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(QPointF(dest_x, dest_y), 4, 4)
        if current_x is not None and current_y is not None:
            # Outer glow (light blue halo)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(66, 133, 244, 60))  # Google blue with transparency
            painter.drawEllipse(QPointF(current_x, current_y), 22, 22)
            # BLUE circle with white border
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.setBrush(QColor(66, 133, 244))  # Google Maps blue
            painter.drawEllipse(QPointF(current_x, current_y), 12, 12)
            # White center dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QPointF(current_x, current_y), 4, 4)
        painter.end()
        self.map_label.setPixmap(pixmap)

    def lat_lon_to_pixel(self, lat, lon, width, height):
        try:
            from math import pi, log, tan, cos
            zoom_level = self.current_zoom
            tile_size = 256
            center_x = (self.current_lon + 180) / 360 * (2 ** zoom_level) * tile_size
            center_y = ((1 - log(tan(self.current_lat * pi / 180) + 1 / cos(self.current_lat * pi / 180)) / pi) / 2) * (2 ** zoom_level) * tile_size
            point_x = (lon + 180) / 360 * (2 ** zoom_level) * tile_size
            point_y = ((1 - log(tan(lat * pi / 180) + 1 / cos(lat * pi / 180)) / pi) / 2) * (2 ** zoom_level) * tile_size
            pixel_x = width / 2 + (point_x - center_x)
            pixel_y = height / 2 + (point_y - center_y)
            return pixel_x, pixel_y
        except Exception as e:
            print(f"Error converting coordinates: {e}")
            return None, None

    def update_gps_status(self):
        if self.gps_connected:
            path_count = len(self.gps_path)
            self.gps_status.setText(
                f"GPS: Connected | Lat: {self.current_lat:.6f}, Lon: {self.current_lon:.6f} | Zoom: {self.current_zoom} | Path: {path_count} pts"
            )
            self.gps_status.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        else:
            self.gps_status.setText(f"GPS:  Waiting for data... | Zoom: {self.current_zoom}")
            self.gps_status.setStyleSheet("color: orange; font-weight: bold; padding: 5px;")

    def show_enlarged_map(self):
        modal = MapModal(self.map_path, self)
        modal.show()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        if self.current_zoom < 19:
            self.current_zoom += 1
            self.mapping_utility.zoom = self.current_zoom
            self.mapping_utility.render_map()
            self.map_path = self.mapping_utility.get_map_path()
            self.base_pixmap = QPixmap(self.map_path)
            self.redraw_markers()
            self.update_gps_status()
            print(f"Zoomed IN to level {self.current_zoom}")

    def zoom_out(self):
        if self.current_zoom > 10:
            self.current_zoom -= 1
            self.mapping_utility.zoom = self.current_zoom
            self.mapping_utility.render_map()
            self.map_path = self.mapping_utility.get_map_path()
            self.base_pixmap = QPixmap(self.map_path)
            self.redraw_markers()
            self.update_gps_status()
            print(f"Zoomed OUT to level {self.current_zoom}")