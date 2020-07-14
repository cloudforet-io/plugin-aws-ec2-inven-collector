from schematics import Model
from schematics.types import StringType, IntType, ListType, DictType


class NIC(Model):
    ip_addresses = ListType(StringType())
    device_index = IntType()
    device = StringType(default="")
    nic_type = StringType()
    cidr = StringType()
    mac_address = StringType()
    public_ip_address = StringType()
    tags = DictType(StringType)
