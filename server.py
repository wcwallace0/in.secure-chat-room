import threading
import socket
import mydb
import time
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

host = "" # localhost
port = 55555
MAX_CONNECTIONS = 5
MAX_CONNECTIONS_PER_MINUTE = 5
connection_history = {} # Store connections timestamps for each IP
banned_ips = []

public_keys = {}

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []

serverClosed = threading.Event()

def broadcast(message):
    for client in clients:
        try:
            recipient_nickname = nicknames[clients.index(client)]
            recipient_key = public_keys.get(recipient_nickname)
            if recipient_key:
                encrypted_message = recipient_key.encrypt(
                    message,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                client.send(encrypted_message)
        except Exception as e:
            continue
                

def handle(client):
    global serverClosed

    while not serverClosed.is_set():
        try:
            # decrypt message here
            message = client.recv(4096)
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
                print(plaintextDecoded)

                # add message to chat history in db
                try:
                    with mydb.db_cursor() as cur:
                        insert_script = 'INSERT INTO message (content) VALUES (%s)'
                        insert_value = (plaintextDecoded,)
                        cur.execute(insert_script, insert_value)
                except Exception as error:
                    print(error)

                broadcast(plaintextDecoded.encode("ascii"))

            except Exception:
                pass  # Message not intended for this client
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f"{nickname} left the chat".encode("ascii"))
            nicknames.remove(nickname)
            break

def receive():
    global serverClosed
    try:
        while not serverClosed.is_set():
            client, address = server.accept()
            client_ip = address[0]

            # Check if user is allowed to join
            # Refuse connection from banned users
            if client_ip in banned_ips:
                print("Client refused: " + client_ip)
                sendOneEncrypted(client, "STOP".encode("ascii"))
                continue

            # Enforce connection limit (DoS protection)
            if len(clients) >= MAX_CONNECTIONS:
                sendOneEncrypted(client, "[Server Busy] Too many connections. Try again later.\n".encode("ascii"))
                time.sleep(0.2)
                sendOneEncrypted(client, "STOP".encode("ascii"))
                continue

            # Check if this ip has exceeded connection threshold
            current_time = time.time()
            if client_ip in connection_history:
                connection_history[client_ip].append(current_time)
                recent_connections = [t for t in connection_history[client_ip] if current_time - t < 60]
                if len(recent_connections) >= MAX_CONNECTIONS_PER_MINUTE:
                    print(f"DoS attack detected from IP: {client_ip}. Banning IP from server.")
                    sendOneEncrypted(client, "STOP".encode("ascii"))
                    # Blacklist/ban IP
                    banned_ips.append(client_ip)
                    continue
            else:
                connection_history[client_ip] = [current_time]

            print(f"Connected with {str(address)}")

            client.send("NICK".encode("ascii"))

            nickname = client.recv(1024).decode("ascii")
            key_data = client.recv(2048)  # Receive public key
            client_public_key = serialization.load_pem_public_key(key_data, backend=default_backend())

            time.sleep(0.2)
            client.send(public_key_bytes)

            nicknames.append(nickname)
            clients.append(client)
            public_keys[nickname] = client_public_key

            print(f"Nickname of the client is {nickname}.")

            # Give connected user a limited message history
            try:
                with mydb.db_cursor() as cur:
                    select_script = 'SELECT content FROM Message ORDER BY message_id DESC LIMIT 10'
                    cur.execute(select_script)
                    sendOneEncrypted(client, messageHistoryString(cur.fetchall()).encode("ascii"))
            except Exception as error:
                print(error)

            broadcast(f"{nickname} joined the chat.".encode("ascii"))
            time.sleep(0.2)
            sendOneEncrypted(client, "Connected to the server.".encode("ascii"))

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
    except Exception as error:
        print(error)
        print("Server closed.")

def write():
    global serverClosed

    while not serverClosed.is_set():
        serverInput = input('')
        if serverInput == "/s":
            # close server
            serverClosed.set()
            print("Stopping the server...")
            broadcast("STOP".encode("ascii"))
            server.close()
            break

def sendOneEncrypted(client, message):
    try:
        recipient_nickname = nicknames[clients.index(client)]
        recipient_key = public_keys.get(recipient_nickname)
        if recipient_key:
            encrypted_message = recipient_key.encrypt(
                message,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            client.send(encrypted_message)
    except Exception as e:
        print(e)
        pass

# Takes a list of the latest messages from the database,
# reverses the order, and concatenates them into a string
# separated by \n
def messageHistoryString(messages):
    if not messages:
        return ""
    history = ""
    for message in messages[::-1]:
        history += message[0] + "\n"
    return history[:-1]

print("Server is listening...")
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()