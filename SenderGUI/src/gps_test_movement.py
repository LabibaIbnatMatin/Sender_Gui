import socket
import time

UDP_IP = "127.0.0.1"  # Use your dashboard's IP if not running locally
UDP_PORT = 5005

# Simulate movement around the map center
base_lat = 23.83778611
base_lon = 90.35948889

# Generate movement: small steps north, east, south, west
movement_data = [
    (base_lat + 0.0001, base_lon),
    (base_lat + 0.0002, base_lon),
    (base_lat + 0.0002, base_lon + 0.0001),
    (base_lat + 0.0001, base_lon + 0.0002),
    (base_lat, base_lon + 0.0002),
    (base_lat - 0.0001, base_lon + 0.0001),
    (base_lat - 0.0002, base_lon),
    (base_lat - 0.0002, base_lon - 0.0001),
    (base_lat - 0.0001, base_lon - 0.0002),
    (base_lat, base_lon - 0.0002),
    (base_lat + 0.0001, base_lon - 0.0001),
    (base_lat + 0.0001, base_lon),
]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for lat, lon in movement_data:
    msg = f"{lat},{lon}"
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))
    print(f"Sent: {msg}")
    time.sleep(0.5)  # Adjust interval as needed

sock.close()
