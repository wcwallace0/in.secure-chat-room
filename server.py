import threading
import socket

host = "127.0.0.1" # localhost
port = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []

serverClosed = threading.Event()

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    global serverClosed

    while not serverClosed.is_set():
        try:
            message = client.recv(1024)
            broadcast(message)
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
            print(f"Connected with {str(address)}")

            client.send("NICK".encode("ascii"))
            nickname = client.recv(1024).decode("ascii")
            nicknames.append(nickname)
            clients.append(client)

            print(f"Nickname of the client is {nickname}.")
            broadcast(f"{nickname} joined the chat.".encode("ascii"))
            client.send("Connected to the server.".encode("ascii"))

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
    except:
        print("Server closed.")

def write():
    global serverClosed

    while not serverClosed.is_set():
        serverInput = input('')
        if serverInput == "/stop":
            # close server
            serverClosed.set()
            print("Stopping the server...")
            broadcast("STOP".encode("ascii"))
            server.close()
            break

print("Server is listening...")
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()