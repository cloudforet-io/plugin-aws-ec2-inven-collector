from schematics import Model
from schematics.types import StringType, DictType, ListType, ModelType, PolyModelType
from spaceone.inventory.model.cloud_service_type import CloudServiceType
from spaceone.inventory.model.server import Server
from spaceone.inventory.model.region import Region

class ErrorResource(Model):
    resource_type = StringType(default='inventory.CloudService')
    provider = StringType(default='aws')
    cloud_service_group = StringType(default='EC2')
    cloud_service_type = StringType(default='Instance')
    resource_id = StringType(serialize_when_none=False)


class ResourceResponse(Model):
    state = StringType()
    message = StringType(default='')
    resource_type = StringType()
    match_rules = DictType(ListType(StringType), serialize_when_none=False)
    resource = DictType(StringType, default={})


class ServerResourceResponse(ResourceResponse):
    state = StringType(default='SUCCESS')
    resource_type = StringType(default='inventory.CloudService')
    match_rules = DictType(ListType(StringType),
                           default={'1': ['reference.resource_id', 'provider', 'cloud_service_type', 'cloud_service_group', 'account']})
    resource = PolyModelType(Server)


class RegionResourceResponse(ResourceResponse):
    state = StringType(default='SUCCESS')
    resource_type = StringType(default='inventory.Region')
    match_rules = DictType(ListType(StringType), default={'1': ['region_code', 'provider']})
    resource = PolyModelType(Region)


class CloudServiceTypeResourceResponse(ResourceResponse):
    state = StringType(default='SUCCESS')
    resource_type = StringType(default='inventory.CloudServiceType')
    match_rules = DictType(ListType(StringType), default={'1': ['name', 'group', 'provider']})
    resource = PolyModelType(CloudServiceType)


class ErrorResourceResponse(ResourceResponse):
    state = StringType(default='FAILURE')
    resource_type = StringType(default='inventory.ErrorResource')
    resource = ModelType(ErrorResource, default={})
