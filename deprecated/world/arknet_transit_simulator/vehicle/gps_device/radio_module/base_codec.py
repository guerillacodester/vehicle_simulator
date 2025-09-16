import time
from typing import Dict, Any
from dataclasses import dataclass, asdict

class BaseCodec:
     def encode(self, packet: Dict[str, Any]) -> bytes:
         raise NotImplementedError
     def decode(self, raw: bytes) -> Dict[str, Any]:
         raise NotImplementedError