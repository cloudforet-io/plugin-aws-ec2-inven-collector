from schematics import Model
from schematics.types import StringType, ModelType, ListType


class CloudWatchDemension(Model):
    name = StringType(serialized_name='Name')
    value = StringType(serialize_when_none='Value')


class CloudWatch(Model):
    class Option:
        serialize_when_none = False

    namespace = StringType()
    dimensions = ListType(ModelType(CloudWatchDemension), default=[])
    region_name = StringType()
