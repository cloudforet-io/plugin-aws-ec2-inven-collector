from schematics import Model
from schematics.types import StringType, IntType, ListType, DictType, ModelType


class NICTags(Model):
    public_dns = StringType(serialize_when_none=False)
    eni_id = StringType(serialize_when_none=False)


class NIC(Model):
    device_index = IntType()
    device = StringType(default="")
    nic_type = StringType()
    ip_addresses = ListType(StringType())
    cidr = StringType()
    mac_address = StringType()
    public_ip_address = StringType()
    tags = ModelType(NICTags, default={})
