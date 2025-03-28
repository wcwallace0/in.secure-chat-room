import threading
import socket
import time

nickname = input("Choose a nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 55555))

leaving = threading.Event()

def receive():
    while not leaving.is_set():
        try:
            message = client.recv(1024).decode("ascii") # receiving from the server
            if message == "NICK":
                client.send(nickname.encode("ascii"))
            elif message == "STOP":
                leave("The chat server has shut down. Disconnecting...\nPress Enter to end the process.")
            else:
                print(message)
        except:
            leave("An error occurred.\nPress Enter to end the process.")

def write():
    while not leaving.is_set():
        userInput = input('')
        if userInput == "/leave":
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