from schematics import Model
from schematics.types import IntType, FloatType, StringType, ListType, BooleanType, DateType


class Hardware(Model):
    core = IntType(default=0)
    memory = FloatType(default=0.0)
