import json


def load_packet(message: bytes):
    json_packet = JsonPacket()
    json_packet.read(message)
    return json_packet


class JsonPacket:

    def __init__(self, _dictionary: dict = None):
        if _dictionary is None:
            _dictionary = {}
        self.dictionary = _dictionary

    def read(self, data: bytes) -> None:
        self.dictionary = json.loads(data.decode("utf-8"))

    def write(self) -> bytes:
        return json.dumps(self.dictionary).encode('utf-8')


if __name__ == '__main__':
    packet = JsonPacket({"name": "Truc", "price": 9})

