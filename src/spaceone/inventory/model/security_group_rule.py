from schematics import Model
from schematics.types import StringType, IntType


class SecurityGroupRule(Model):
    protocol = StringType()
    remote = StringType()
    remote_id = StringType()
    security_group_name = StringType()
    port_range_min = IntType()
    port_range_max = IntType()
    security_group_id = StringType()
    description = StringType()
    direction = StringType()
    port = StringType()
