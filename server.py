import threading
import socket
import mydb
import time

host = "" # localhost
port = 55555
MAX_CONNECTIONS = 20
MAX_CONNECTIONS_PER_MINUTE = 20
connection_history = {} # Store connections timestamps for each IP
banned_ips = []

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

            # add message to chat history in db
            print(message.decode("ascii"))
            try:
                with mydb.db_cursor() as cur:
                    insert_script = 'INSERT INTO message (content) VALUES (%s)'
                    insert_value = (message.decode("ascii"),)
                    cur.execute(insert_script, insert_value)
            except Exception as error:
                print(error)

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
            client_ip = address[0]

            # Check if user is allowed to join
            # Refuse connection from banned users
            if client_ip in banned_ips:
                client.send("STOP".encode("ascii"))
                continue

            # Enforce connection limit (DoS protection)
            if len(clients) >= MAX_CONNECTIONS:
                client.send("[Server Busy] Too many connections. Try again later.\n".encode("ascii"))
                time.sleep(0.2)
                client.send("STOP".encode("ascii"))
                continue

            # Check if this ip has exceeded connection threshold
            current_time = time.time()
            if client_ip in connection_history:
                connection_history[client_ip].append(current_time)
                recent_connections = [t for t in connection_history[client_ip] if current_time - t < 60]
                if len(recent_connections) >= MAX_CONNECTIONS_PER_MINUTE:
                    print(f"DoS attack detected from IP: {client_ip}. Banning IP from server.")
                    client.send("STOP".encode("ascii"))
                    # Blacklist/ban IP
                    banned_ips.append(client_ip)
                    continue
            else:
                connection_history[client_ip] = [current_time]

            print(f"Connected with {str(address)}")

            client.send("NICK".encode("ascii"))
            nickname = client.recv(1024).decode("ascii")
            nicknames.append(nickname)
            clients.append(client)

            print(f"Nickname of the client is {nickname}.")

            # Give connected user a limited message history
            try:
                with mydb.db_cursor() as cur:
                    select_script = 'SELECT content FROM Message ORDER BY message_id DESC LIMIT 10'
                    cur.execute(select_script)
                    client.send(messageHistoryString(cur.fetchall()).encode("ascii"))
            except Exception as error:
                print(error)

            broadcast(f"{nickname} joined the chat.".encode("ascii"))
            time.sleep(0.2)
            client.send("Connected to the server.".encode("ascii"))

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
    except:
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