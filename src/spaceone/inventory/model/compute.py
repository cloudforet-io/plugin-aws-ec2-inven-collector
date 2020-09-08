from schematics import Model
from schematics.types import  StringType, DateTimeType, ListType, BooleanType, ModelType, DictType


class ComputeTags(Model):
    arn = StringType(serialize_when_none=False)


class Compute(Model):
    keypair = StringType()
    az = StringType()
    instance_state = StringType(choices=('pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped'))
    instance_type = StringType()
    launched_at = DateTimeType()
    instance_id = StringType(default='')
    instance_name = StringType(default='')
    security_groups = ListType(DictType(StringType()))
    image = StringType()
    account = StringType()
    tags = ModelType(ComputeTags, default={})
