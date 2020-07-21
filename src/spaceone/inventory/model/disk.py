from schematics import Model
from schematics.types import StringType, IntType, DictType, BooleanType


class Disk(Model):
    device_index = IntType()
    device = StringType()
    disk_type = StringType(default="EBS")
    size = IntType()
    tags = DictType(StringType(), default={})


