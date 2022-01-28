"""A client to talk to foreman server"""

import socket


class Client:

    def __init__(self, addr):
        self.sock, self.addr = None, addr

    def say(self, message):
        """
        Base method to communicate with foreman-server.
        Auto-connects if needed.

        Args:
            message (str): message to send

        Returns:
            str: response from server
        """
        if not self.sock:
            self.sock = socket.socket()
            self.sock.settimeout(8)
            self.sock.connect(self.addr)
        # Enforce single LF at the end of our message:
        self.sock.sendall(message.rstrip("\n").encode() + b"\n")

        # Double LF denotes end of response
        buff = b""
        while b"\n\n" not in buff:  # IDEA: avoid scan entire buff on each recv?
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
        """
        Ask foreman-server permission to take `name`.

        Args:
            name (str): resource name to claim

        Returns:
            bool: True - take is successful. False - name already taken.

        If foreman responds `name 0` -- noone's been asking it yet. We take it.
        Otherwise foreman says `name 1` -- it's been claimed before. Take fails.
        """
        resp = self.say(f"take {name}")
        # Response comes in format: `{name} <zero or one>`
        resp_name, taken = resp[:-2], resp[-1]
        assert name == resp_name, "Take name mismatch"
        # Zero means: noone else claimed {name} yet, take is successful.
        return int(taken) == 0

    def stop_foreman(self):
        self.say("thank you")
