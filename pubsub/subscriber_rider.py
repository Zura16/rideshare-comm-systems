import socket

#create a UDP socket to listen for messages from the publisher
HOST, PORT = "127.0.0.1", 5001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
print(f"listening on udp://{HOST}:{PORT}")
#listen forever
while True:
    data, addr = sock.recvfrom(65535)
    print("recv from", addr, data.decode("utf-8", errors="replace"))
