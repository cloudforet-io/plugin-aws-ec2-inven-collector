from schematics import Model
from schematics.types import StringType, IntType, DictType, BooleanType


class Disk(Model):
    volume_id = StringType()
    device_index = IntType()
    device = StringType()
    disk_type = StringType(default="EBS")
    volume_type = StringType(choices=('standard', 'io1', 'gp2', 'sc1', 'st1'))
    size = IntType()
    iops = IntType(serialize_when_none=False)
    encrypted = BooleanType()
    tags = DictType(StringType(), default={})
