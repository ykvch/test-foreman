"""A client to talk to foreman server"""

import socket


class Client:

    def __init__(self, addr):
        self.sock, self.addr = None, addr

    def say(self, message):
        if not self.sock:
            self.sock = socket.socket()
            self.sock.settimeout(8)
            self.sock.connect(self.addr)
        # Enforce single LF at the end of our message:
        self.sock.sendall(message.rstrip("\n").encode() + b"\n")

        # Double LF denotes end of response
        buff = b""
        while b"\n\n" not in buff:
            resp = self.sock.recv(1024)
            if not resp:
                self.close()
                raise ConnectionError("Foreman closed connection")
            buff += resp

        return buff.partition(b"\n\n")[0].decode()

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def take(self, name):
        resp = self.say(f"take {name}")
        resp_name, taken = resp[:-2], resp[-1]
        assert name == resp_name, "Take name mismatch"
        return int(taken) == 0

    def stop_foreman(self):
        self.say("thank you")
