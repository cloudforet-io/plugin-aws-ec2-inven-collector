from schematics import Model
from schematics.types import  StringType, DateTimeType, ListType, BooleanType


class Compute(Model):
    eip = ListType(StringType())
    keypair = StringType()
    az = StringType()
    instance_state = StringType(choices=('pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped'))
    instance_type = StringType()
    launched_at = DateTimeType()
    region_name = StringType()
    instance_id = StringType()
    instance_name = StringType(default='')
    termination_protection = BooleanType()
    security_groups = ListType(StringType())
    image = StringType()
    account_id = StringType()
