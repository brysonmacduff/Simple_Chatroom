from enum import Enum

class MessageTypes(Enum):
    CHAT = 1
    HEARTBEAT = 2

    def __int__(self):
        return self.value