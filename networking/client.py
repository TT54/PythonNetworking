import socket
import time
from typing import Optional

import select
from networking.packet import *
import struct
import threading


class Client:

    def __init__(self, _host, _port, _header_size=4):
        self.host = _host
        self.port = _port
        self.header_size = _header_size
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.enabled = False

    def send_packet(self, message: JsonPacket):
        if not self.enabled:
            return None
        encoded_message = message.write()
        message_length = struct.pack('!I', len(encoded_message))
        self.client_socket.sendall(message_length + encoded_message)

    def read_packet(self, client_socket: socket.socket) -> Optional[JsonPacket]:
        try:
            raw_message_length = client_socket.recv(self.header_size)
            if not raw_message_length:
                return None
            message_length = struct.unpack('!I', raw_message_length)[0]

            data = b''
            while len(data) < message_length:
                data_part = client_socket.recv(min(1024, message_length - len(data)))
                if not data_part:
                    return None
                data += data_part

            json_packet = packet.load_packet(data)

            return json_packet
        except:
            return None

    def launch_thread(self):
        self.client_socket.connect((self.host, self.port))
        print(f"Client connecté au serveur {self.host}:{self.port}")
        self.enabled = True

        test_packet = JsonPacket({"message": "Ceci est un test"})
        self.send_packet(test_packet)

        while True:
            read_sockets, _, _ = select.select([self.client_socket], [], [])

            for notified_socket in read_sockets:
                if notified_socket == self.client_socket:
                    # Message reçu du serveur
                    message = self.read_packet(self.client_socket)
                    if message is None:
                        print("Déconnecté du serveur")
                        self.client_socket.close()
                        return None
                    else:
                        print(f"Message reçu: {message}")

    def enable_client(self):
        input_thread = threading.Thread(target=self.launch_thread)
        input_thread.daemon = False  # Le thread ne se termine pas quand le thread principal termine
        input_thread.start()


if __name__ == '__main__':
    client = Client("127.0.0.1", 12345)
    client.enable_client()
    print("ok ?")
    while not client.enabled:
        time.sleep(0.1)
    client.send_packet(JsonPacket({"allo": "alluile !"}))
