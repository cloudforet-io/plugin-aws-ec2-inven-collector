from schematics import Model
from schematics.types import ListType, StringType, ModelType


class CloudTrailLookupResource(Model):
    AttributeKey = StringType(default='ResourceName')
    AttributeValue = StringType(default='')


class CloudTrail(Model):
    region_name = StringType(serialize_when_none=False)
    resource_type = StringType(serialize_when_none=False)
    LookupAttributes = ListType(ModelType(CloudTrailLookupResource), default=[])
