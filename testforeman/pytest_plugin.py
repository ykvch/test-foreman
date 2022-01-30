import logging
import os
import socket
from .client import Client

log = logging.getLogger('pytest.plugins.foreman')


def pytest_addoption(parser):
    group = parser.getgroup("foreman")
    group.addoption("--with-foreman", action="store_true",
                    dest="foreman", help="Run as testforeman client")
    group.addoption("--foreman-addr", dest="foreman_addr",
                    metavar="host:port", default=os.environ.get(
                        "FOREMAN_ADDR", "localhost:7788"),
                    help="Foreman server to sync with")


# Ref: https://github.com/pytest-dev/pytest/issues/3261#issuecomment-369740536

class ForemanPlugin:
    """Simple plugin to sync test workers with server"""

    def __init__(self, config):
        # TODO: handle IPv6 nicely
        host, port = config.option.foreman_addr.rsplit(":", 1)
        port = int(port)
        self.client = Client((host, port))

    def pytest_sessionfinish(self):
        self.client.close()

    def pytest_runtest_protocol(self, item, nextitem):
        # Anything except None would skip the test
        return None if self.client.take(item.name) else False


def pytest_configure(config):
    if config.option.foreman:
        config.pluginmanager.register(ForemanPlugin(config))
