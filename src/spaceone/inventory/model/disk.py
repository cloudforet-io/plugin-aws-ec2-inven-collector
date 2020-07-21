from schematics import Model
from schematics.types import StringType, IntType, BooleanType, ModelType


class DiskTags(Model):
    volume_id = StringType(serialize_when_none=False)
    volume_type = StringType(choices=('standard', 'io1', 'gp2', 'sc1', 'st1'), serialize_when_none=False)
    encrypted = BooleanType(serialize_when_none=False)
    iops = IntType(serialize_when_none=False)


class Disk(Model):
    device_index = IntType()
    device = StringType()
    disk_type = StringType(default="EBS")
    size = IntType()
    tags = ModelType(DiskTags, default={})


