from schematics import Model
from schematics.types import StringType, IntType, ListType, DictType

class NIC(Model):
    device_index = IntType()
    device = StringType(default="")
    nic_type = StringType()
    ip_addresses = ListType(StringType())
    cidr = StringType()
    mac_address = StringType()
    public_ip_address = StringType()
    tags = DictType(StringType, default={})
