## About In.Secure Chat Room
In.Secure Chat Room is a chat room application that utilizes Python sockets to allow users to communicate over a chat room server. This repository contains two versions of the app: a secure and insecure version, available in their respective branches. The insecure branch takes little security precautions and allows for three specific vulnerabilities: SQL injection, susceptibility to denial-of-service (DoS) attacks, and the lack of end-to-end encryption. The secure branch takes the proper precautions against these vulnerabilities.

The purpose of this project is to analyze and demonstrate the issues these vulnerabilities propose, as well as how to protect against them. 


## Running the Server
To run the server, use the command: python3 server.py
To stop the server, type /s into the server terminal


## Connecting to the Server
To connect to the server, use the command in a separate terminal: python3 client.py
To leave the chat room, type /l into the client terminal
