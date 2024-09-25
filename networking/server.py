import socket
from typing import Optional

import select
import struct
from networking.packet import *

HEADER_SIZE = 4


class Server:

    registered_packets = {}

    def __init__(self, _host, _port):
        self.host = _host
        self.port = _port
        self.sockets = []
        self.clients = {}

    def add_new_connection(self, server_socket):
        client_socket, client_address = server_socket.accept()
        self.sockets.append(client_socket)
        self.clients[client_socket] = client_address
        print(f"Nouvelle connexion de {client_address}")

    def disconnect(self, client_socket: socket.socket):
        self.sockets.remove(client_socket)
        print(f"Déconnexion de {self.clients[client_socket]}")
        self.clients.pop(client_socket)
        client_socket.close()

    def send_packet(self, client_socket, message: JsonPacket):
        encoded_message = message.write()
        message_length = struct.pack('!I', len(encoded_message))
        packet_id = struct.pack("!I", message.packet_id)
        client_socket.sendall(message_length + packet_id + encoded_message)

    def read_packet(self, client_socket: socket.socket) -> Optional[JsonPacket]:
        try:
            raw_message_length = client_socket.recv(HEADER_SIZE)
            if not raw_message_length:
                return None
            message_length = struct.unpack('!I', raw_message_length)[0]

            raw_packet_id = client_socket.recv(HEADER_SIZE)
            if not raw_packet_id:
                return None
            packet_id = struct.unpack("!I", raw_packet_id)[0]

            data = b''
            while len(data) < message_length:
                data_part = client_socket.recv(min(1024, message_length - len(data)))
                if not data_part:
                    return None
                data += data_part

            json_packet = load_packet(packet_id, data)
            if packet_id in self.registered_packets.keys():
                back_packet = self.registered_packets[packet_id](json_packet)
                if back_packet is not None:
                    self.send_packet(client_socket, back_packet)

            return json_packet
        except:
            return None

    def enable_sockets(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        print(f"Début de l'écoute sur {self.host}:{self.port}")
        server_socket.setblocking(False)
        self.sockets.append(server_socket)

        try:
            while True:
                read_sockets, _, exception_sockets = select.select(self.sockets, [], [])
                for available_socket in read_sockets:
                    if available_socket == server_socket:
                        self.add_new_connection(available_socket)
                    else:
                        message = self.read_packet(available_socket)
                        if message is None:
                            self.disconnect(available_socket)
                        else:
                            print(message.dictionary)

                for errored_socket in exception_sockets:
                    self.disconnect(errored_socket)
        except KeyboardInterrupt:
            print("Interruption manuelle")

    def register_packet(self, packet_id: int, response: callable(JsonPacket)):
        self.registered_packets[packet_id] = response
        print(self.registered_packets.keys())


def hello_world_packet_handler(message: JsonPacket):
    sender = message.dictionary['sender']
    print(f"Hello world received from {sender}")
    hello_back = JsonPacket(2, {"content": f"Hello {sender}"})
    return hello_back


if __name__ == '__main__':
    server = Server("127.0.0.1", 12345)
    server.register_packet(1, hello_world_packet_handler)
    server.enable_sockets()
