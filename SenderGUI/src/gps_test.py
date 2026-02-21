import socket
import time

UDP_IP = "0.0.0.0"  # Use your dashboard's IP if not running locally
UDP_PORT = 5005

# Example GPS data sequence
gps_data = [
    (23.8383014, 90.3592221),
    (23.8383019, 90.3592215),
    (23.8383014, 90.3592219),
    (23.8383014, 90.3592220),
    (23.8383017, 90.3592214),
    (23.8383023, 90.3592215),
    (23.8383029, 90.3592215),
    (23.8383041, 90.3592216),
    # ... add more tuples as needed ...
]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for lat, lon in gps_data:
    msg = f"{lat},{lon}"
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))
    print(f"Sent: {msg}")
    time.sleep(0.5)  # Adjust interval as needed

sock.close()