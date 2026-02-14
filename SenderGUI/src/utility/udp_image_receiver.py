import socket
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class UDPImageReceiver(QObject):
    image_received = pyqtSignal(bytes)

    def __init__(self, ip='192.168.68.115', port=5007):   #here the ip and port will be orin's(receiverside) setting it to 0.0.0.0 means it will hear from all of the available interefaces
        super().__init__()                         #here orins' ip is 192.168.1.116 and port is 5006
        self.ip = ip
        self.port = port
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.ip, self.port))
        while self.running:
            data, _ = sock.recvfrom(65536)  # Adjust buffer size as needed
            self.image_received.emit(data)

    def stop(self):
        self.running = False