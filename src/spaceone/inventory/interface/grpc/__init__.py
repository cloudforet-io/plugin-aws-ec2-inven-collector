from spaceone.core.pygrpc.server import GRPCServer
from .collector import Collector

__all__ = ['app']

app = GRPCServer()
app.add_service(Collector)