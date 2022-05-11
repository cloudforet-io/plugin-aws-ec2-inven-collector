from schematics import Model
from schematics.types import ListType, StringType, PolyModelType, DictType, BooleanType
from spaceone.inventory.model import CloudServiceTypeMetadata


class CloudServiceType(Model):
    name = StringType(default='Instance')
    provider = StringType(default='aws')
    group = StringType(default='EC2')
    labels = ListType(StringType(), serialize_when_none=False, default=['Compute', 'Server'])
    tags = DictType(StringType, serialize_when_none=False)
    is_primary = BooleanType(default=True)
    is_major = BooleanType(default=True)
    service_code = StringType(default='AmazonEC2')
    resource_type = StringType(default='inventory.CloudService')
    _metadata = PolyModelType(CloudServiceTypeMetadata, serialize_when_none=False, serialized_name='metadata')
