import json
import random
import socket
import time

#create a UDP socket to send messages to the subscriber
HOST, PORT = "127.0.0.1", 5001
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def main():
    driver_id = "d-001"
    x = 5
    # send 5 messages then exit
    while x != 0:
        msg = {
            "driver_id": driver_id,
            "lat": 33.78 + random.random()/100,
            "lon": -118.11 + random.random()/100,
            "status": "available"
        }
        sock.sendto(json.dumps(msg).encode(), (HOST, PORT))
        print("sent", msg)
        time.sleep(1)
        x -= 1


if __name__ == "__main__":
    main()
