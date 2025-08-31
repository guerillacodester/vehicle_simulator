import json
from  ..base import BaseCodec

class JsonCodec(BaseCodec):
    def encode(self, packet):
        return json.dumps(packet).encode("utf-8")

    def decode(self, raw):
        return json.loads(raw.decode("utf-8"))
