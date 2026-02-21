import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QIcon
from ui.dashboard_ui import DashboardUI
from utility.listen_to_udp import UDPListener

class AppLogic(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Autonomous Dashboard")
        # self.setWindowIcon(QIcon("/home/labiba-ibnat-matin/Downloads/mongol_barota.png"))  
        # self.resize(1200, 1200)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.ui = DashboardUI()
        self.ui.setup_ui(self.central_widget)
        
        # Start UDP listener to receive GPS from ReceiverGUI
        self.udp_listener = UDPListener(ip="0.0.0.0", port=5005)
        self.udp_listener.gps_data_received.connect(self.on_gps_received)
        self.udp_listener.start()
        print("UDP Listener started on port 5005")
    
    def on_gps_received(self, lat, lon):
        """Handle GPS data received from ReceiverGUI"""
        print(f"Main: Received GPS - Lat: {lat}, Lon: {lon}")
        # Pass GPS to dashboard UI
        self.ui.on_gps_received(lat, lon)
    
    def closeEvent(self, event):
        """Stop UDP listener when closing"""
        print("Stopping UDP listener...")
        self.udp_listener.stop()
        self.udp_listener.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppLogic()
    window.show()
    sys.exit(app.exec())