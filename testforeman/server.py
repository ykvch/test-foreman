import sys
import socket
import asyncore
import logging
import fnmatch

LOG = logging.getLogger('testforeman')
logging.basicConfig(
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s', level='DEBUG')


class ForemanHandler(asyncore.dispatcher_with_send):

    def __init__(self, sock, master):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.master = master
        self.buffer = b''

    def handle_read(self):  # this method works with bytes
        head, sep, tail = self.recv(1024).partition(b'\n')

        while sep:  # handle case of multiple lines in one recv
            self.dispatch_req(self.buffer + head)
            self.buffer = b''
            head, sep, tail = tail.partition(b'\n')
        # if something remains without \n, store it for the next handle_read
        self.buffer += head

    def dispatch_req(self, req):
        '''Parse request and call appropriate method to handle it
        req: request bytes (command arg0 arg1 arg2)
        '''
        cmd = req.decode().split()
        LOG.debug('{0}: {1}'.format(self.addr, req))
        return getattr(self, cmd[0])(*cmd[1:])

    def thank(self, who): # shut down the server by "thank you" command
        if who != "you":
            raise AttributeError("Shutdown command should be: `thank you`")
        for m in list(asyncore.socket_map.values()):
            m.close()

    def take(self, item):
        # We register node only if tries to "take" file
        # Also ensures that previously deleted node would be re-registered
        node = self.master.taken.setdefault('{0}:{1}'.format(*self.addr), set())
        taken_already = any(item in r for r in list(self.master.taken.values()))
        if not taken_already:
            node.add(item)
        self.send('{0} {1:d}\n'.format(item, taken_already).encode())
        LOG.info('{0}: {1} {2}'.format(self.addr, item,
                                       'already taken' if taken_already else 'OK'))

    def ls(self, pattern='*', node='*'):
        for k, v in list(self.master.taken.items()):
            if not fnmatch.fnmatch(k, node):
                continue
            fnlist = fnmatch.filter(v, pattern)
            if fnlist:
                self.send('[{0}]\n'.format(k).encode())
                for i in fnlist:
                    self.send('{0}\n'.format(i).encode())
        self.send(b'\n')

    def rm(self, pattern=''):
        k, v = list(self.master.taken.keys()), list(self.master.taken.values())
        rm_list = [fnmatch.filter(i, pattern) for i in v]
        for r, k, v in zip(rm_list, k, v):
            self.master.taken[k] = v.difference(r)
        self.send('{0}\n'.format(sum(len(x) for x in rm_list)).encode())

    def nodes(self):
        for k, v in list(self.master.taken.items()):
            self.send('{0} {1}\n'.format(k, len(v)).encode())
        self.send(b'\n')

    def rmnode(self, node):
        if node in self.master.taken:
            del self.master.taken[node]
            self.send(b'1\n')
        else:
            self.send(b'0\n')

    def help(self):
        self.send(b'Available commands: help,take,ls,nodes,thank you,rmnode,rm\n')


class ForemanServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(8)
        self.taken = {}

    def handle_accept(self):
        sock_addr = self.accept()
        if sock_addr is None:
            return
        sock, addr = sock_addr
        LOG.info('Incoming connection from {0}:{1}'.format(*addr))
        ForemanHandler(sock, self)


def main():
    args = dict(zip(('progname', 'host', 'port'), sys.argv))
    ForemanServer(args.get('host', 'localhost'), int(args.get('port', 8888)))
    asyncore.loop()


if __name__ == '__main__':
    main()
