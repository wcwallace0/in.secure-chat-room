import threading
import socket
import psycopg2
from dotenv import dotenv_values

config = dotenv_values(".env")

host = "" # localhost
port = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []

conn = None

serverClosed = threading.Event()

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    global serverClosed

    while not serverClosed.is_set():
        try:
            message = client.recv(1024)

            # add message to chat history in db
            print(message.decode("ascii"))
            try:
                with psycopg2.connect(
                            host = config["HOSTNAME"],
                            dbname = config["DATABASE"],
                            user = config["USER"],
                            password = config["PASSWORD"],
                            port = config["PORT"]) as conn:

                    with conn.cursor() as cur:

                        insert_script = 'INSERT INTO message (content) VALUES (%s)'
                        insert_value = (message.decode("ascii"),)
                        cur.execute(insert_script, insert_value)

            except Exception as error:
                print(error)
            finally:
                if conn is not None:
                    conn.close()

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