from schematics import Model
from schematics.types import IntType


class Hardware(Model):
    core = IntType()
    memory = IntType()
