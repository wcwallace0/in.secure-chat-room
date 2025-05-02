import threading
import socket
import time
from dotenv import dotenv_values
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

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

config = dotenv_values(".env")

nickname = input("Choose a nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 55555))
# client.connect((config["IP"], 55555))

leaving = threading.Event()

def receive():
    while not leaving.is_set():
        try:
            message = client.recv(4096) # receiving from the server
            if message == b"NICK":
                client.send(nickname.encode("ascii"))
                time.sleep(0.1)
                client.send(public_key_bytes)
            else:
                try:
                    # Attempt to decrypt incoming message
                    plaintext = private_key.decrypt(
                        message,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                        )
                    )

                    plaintextDecoded = plaintext.decode("utf-8")
                    if plaintextDecoded == "STOP":
                        leave("The chat server has shut down. Disconnecting...\nPress Enter to end the process.")
                    else:
                        print(plaintextDecoded)
                except Exception:
                    pass  # Message not intended for this client
        except Exception as error:
            print(error)
            leave("An error occurred.\nPress Enter to end the process.")

def write():
    while not leaving.is_set():
        userInput = input('')
        if userInput == "/l":
            leave("Leaving the chat room...")
        elif leaving.is_set():
            break
        else:
            message = f"{nickname}: {userInput}"
            client.send(message.encode("ascii"))

def leave(message):
    if not leaving.is_set():
        leaving.set()
        print(message)
        client.close()

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()