from schematics import Model
from schematics.types import StringType, IntType, DictType, PolyModelType


class Disk(Model):
    device_index = IntType()
    device = StringType()
    disk_type = StringType(choices=('standard', 'io1', 'gp2', 'sc1', 'st1'))
    size = IntType()
    tags = DictType(PolyModelType([StringType, IntType]))
