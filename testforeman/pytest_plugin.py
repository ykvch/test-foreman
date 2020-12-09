import logging
import os
import socket

log = logging.getLogger('pytest.plugins.foreman')


def pytest_addoption(parser):
    group = parser.getgroup("foreman")
    group.addoption("--with-foreman", action="store_true",
                    dest="foreman", help="Run as testforeman client")
    group.addoption("--foreman-addr", dest="foreman_addr",
                    metavar="host:port", default=os.environ.get(
                        "FOREMAN_ADDR", "localhost:7777"),
                    help="Foreman server to sync with")


class ForemanPlugin:
    """Simple plugin to sync test workers with server"""

    def __init__(self, config):
        host, port = config.option.foreman_addr.rsplit(":", 1)
        port = int(port)
        self.client = socket.socket()
        self.client.connect((host, port))

    def pytest_sessionfinish(self):
        self.client.close()

    def pytest_testnodedown(self, node, error):
        """standard xdist hook function.
        """


def pytest_configure(config):
    if config.option.foreman:
        config.pluginmanager.register(ForemanPlugin(config))
