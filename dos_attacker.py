import socket
import threading
import time

SERVER_IP = "127.0.0.1"
PORT = 55555

def flood():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, PORT))
        s.send(b"DoSUser")
        while True:
            pass
    except Exception as e:
        print("kicked from server")
        pass  # Connection might get refused or dropped

# Create multiple threads to simulate flood
for i in range(5):  # Try increasing this number for stronger impact
    thread = threading.Thread(target=flood)
    thread.start()