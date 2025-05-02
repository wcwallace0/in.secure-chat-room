import threading
import socket
import psycopg2
import mydb

host = "" # localhost
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
    if(not messages):
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