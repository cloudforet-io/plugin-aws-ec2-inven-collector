from schematics import Model
from schematics.types import StringType, ModelType, ListType


class CloudWatchDimension(Model):
    Name = StringType(serialize_when_none=False)
    Value = StringType(serialize_when_none=False)


class CloudWatchMetricInfo(Model):
    Namespace = StringType(serialize_when_none=False)
    Dimensions = ListType(ModelType(CloudWatchDimension), serialize_when_none=False)


class CloudWatch(Model):
    region_name = StringType(default='us-east-1')
    metrics_info = ListType(ModelType(CloudWatchMetricInfo), default=[])
