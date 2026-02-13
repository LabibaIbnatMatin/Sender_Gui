import cv2
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)

    def __init__(self, stream_url):
        super().__init__()
        self.stream_url = stream_url
        self.running = False

    def run(self):
        cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
        self.running = True
        
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                self.frame_ready.emit(qimg)
            self.msleep(30)
        
        cap.release()

    def stop(self):
        self.running = False
        self.wait()

class CameraFeed(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Camera preview
        self.preview = QLabel("Camera: Waiting for streams...")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("background: black; color: gray; min-height: 200px; font-size: 12px;")
        layout.addWidget(self.preview)
        
        # Controls
        ctrl = QHBoxLayout()
        
        # Dropdown for stream selection
        self.stream_combo = QComboBox()
        self.stream_combo.addItem("No streams found", None)
        ctrl.addWidget(self.stream_combo)
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.start_stream)
        self.play_btn.setEnabled(False)
        ctrl.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_stream)
        self.stop_btn.setEnabled(False)
        ctrl.addWidget(self.stop_btn)
        
        layout.addLayout(ctrl)
        
        self.thread = None
        self.cameras = []

    def update_streams(self, cameras):
        """Called when discovery finds new cameras"""
        self.cameras = cameras
        current_url = self.stream_combo.currentData()
        
        self.stream_combo.clear()
        
        if not cameras:
            self.stream_combo.addItem("No streams found", None)
            self.play_btn.setEnabled(False)
            self.preview.setText("Camera: No streams detected")
            return
        
        # Add all discovered streams
        for cam in cameras:
            label = cam.get('label', 'Unknown')
            url = cam.get('rtsp_url')
            codec = cam.get('codec', 'H264')
            
            display_text = f"{label} [{codec}]"
            self.stream_combo.addItem(display_text, url)
        
        # Re-select previous stream if it still exists
        if current_url:
            for i in range(self.stream_combo.count()):
                if self.stream_combo.itemData(i) == current_url:
                    self.stream_combo.setCurrentIndex(i)
                    break
        
        self.play_btn.setEnabled(True)
        self.preview.setText(f"Camera: {len(cameras)} stream(s) available")
        print(f"[CameraFeed] Updated with {len(cameras)} streams")

    def start_stream(self):
        url = self.stream_combo.currentData()
        if not url:
            self.preview.setText(" No stream selected")
            return
            
        self.stop_stream()
        self.preview.setText("🔄 Connecting...")
        
        self.thread = CameraThread(url)
        self.thread.frame_ready.connect(self.update_frame)
        self.thread.start()
        
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        print(f"[CameraFeed] Starting stream: {url}")

    def stop_stream(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
        self.preview.setPixmap(QPixmap())
        self.preview.setText("Camera: Stopped")
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        print("[CameraFeed] Stream stopped")

    def update_frame(self, qimg):
        pix = QPixmap.fromImage(qimg).scaled(
            640, 360, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.preview.setPixmap(pix)