import socket
import threading
import time
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

SERVER_IP = "127.0.0.1"
PORT = 55555

# Generate RSA Key Pair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

public_key = private_key.public_key()
public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

def flood():
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, PORT))
        time.sleep(1)
        s.send("nick".encode("ascii"))
        s.send(public_key_bytes)
        time.sleep(1)
        s.close()
        print("connection closed")

# Create multiple threads to simulate flood
# for i in range(5):  # Try increasing this number for stronger impact
#     thread = threading.Thread(target=flood)
#     thread.start()

flood()