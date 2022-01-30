#!/usr/bin/env
# -*- coding: utf-8 -*-

import logging
import os
from fnmatch import fnmatch
import socket
from nose.plugins import Plugin

log = logging.getLogger('nose.plugins.foreman')


class ForemanClient(Plugin):
    name = 'foreman'
    reg_addr, sock = None, None

    def configure(self, options, conf):
        super(ForemanClient, self).configure(options, conf)
        if not self.enabled:
            return
        self.sock = None
        host, port = options.foreman_server.rsplit(':', 1)
        self.reg_addr = host, int(port)
        self.pattern = options.foreman_fnmatch
        self.ignore = options.foreman_fnignore
        self.connect_to_server()

    def connect_to_server(self):
        '''Creates client socket and connects to foreman server
        defined in plugin options (see options method)'''
        self.sock = socket.socket()
        self.sock.settimeout(10)
        try:
            self.sock.connect(self.reg_addr)
        except socket.error:
            raise RuntimeError(
                'Failed to connect to foreman server at {0}'.format(self.reg_addr))

    def options(self, parser, env):
        super(ForemanClient, self).options(parser, env)
        parser.add_option('--foreman-server',
                          default=env.get('FOREMAN_ADDR', 'localhost:7788'),
                          dest='foreman_server',
                          metavar='host:port',
                          help='Running foreman server network address')
        parser.add_option('--foreman-match',
                          default=env.get('FOREMAN_FNMATCH', 'test*'),
                          dest='foreman_fnmatch',
                          metavar='pattern',
                          help='Pattern to match for test-containing modules')
        parser.add_option('--foreman-ignore',
                          default=env.get('FOREMAN_FNIGNORE', ''),
                          dest='foreman_fnignore',
                          metavar='pattern',
                          help='Pattern to ignore for test-containing modules')

    def finalize(self, result):
        self.sock.close()

    def wantModule(self, mod):
        # https://docs.python.org/3/reference/import.html#packages
        if hasattr(mod, '__path__'):
            return None
        bname = mod.__name__
        # bname = os.path.basename(mod)
        if not fnmatch(bname, self.pattern) or fnmatch(bname, self.ignore):
            return False

        self.sock.sendall('take ' + bname + '\n')
        data = resp = self.sock.recv(1024)
        while '\n' not in resp:
            resp = self.sock.recv(1024)
            if not resp:  # reconnect
                self.connect_to_server()
            data += resp

        head, _, _ = data.partition('\n')
        recv_name, taken = head[:-2], head[-1]
        assert recv_name == bname, 'Got incorrect module name from foreman server'

        if int(taken):  # already taken by someone else
            return False  # so we don't want that module
        # else: return None # meaning: let the selector decide
