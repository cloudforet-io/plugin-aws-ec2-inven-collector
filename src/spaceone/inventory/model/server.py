from schematics import Model
from schematics.types import ModelType, ListType, StringType, PolyModelType, DateTimeType, FloatType, DictType, BaseType
from spaceone.inventory.model import OS, AWS, Hardware, SecurityGroup, Compute, LoadBalancer, VPC, Subnet, \
    AutoScalingGroup, NIC, Disk, ServerMetadata, CloudWatch, CloudTrail


class ReferenceModel(Model):
    class Option:
        serialize_when_none = False

    resource_id = StringType(required=False, serialize_when_none=False)
    external_link = StringType(required=False, serialize_when_none=False)


class ServerData(Model):
    os = ModelType(OS)
    aws = ModelType(AWS)
    hardware = ModelType(Hardware)
    security_group = ListType(ModelType(SecurityGroup))
    compute = ModelType(Compute)
    load_balancer = ListType(ModelType(LoadBalancer))
    vpc = ModelType(VPC)
    subnet = ModelType(Subnet)
    auto_scaling_group = ModelType(AutoScalingGroup, serialize_when_none=False)
    nics = ListType(ModelType(NIC))
    disks = ListType(ModelType(Disk))
    primary_ip_address = StringType(default='')
    cloudwatch = ModelType(CloudWatch, serialize_when_none=False)
    cloudtrail = ModelType(CloudTrail, serialize_when_none=False)


class Server(Model):
    name = StringType(default='')
    region_code = StringType()
    data = ModelType(ServerData)
    tags = DictType(StringType, default={})
    ip_addresses = ListType(StringType())
    account = StringType()
    type = StringType(serialize_when_none=False)
    size = StringType(serialize_when_none=False)
    launched_at = DateTimeType(serialize_when_none=False)
    server_type = StringType(default='VM')
    provider = StringType(default='aws')
    cloud_service_type = StringType(default='Instance')
    cloud_service_group = StringType(default='EC2')
    instance_type = StringType(serialize_when_none=False)
    instance_size = FloatType(serialize_when_none=False)
    _metadata = PolyModelType(ServerMetadata, serialized_name='metadata', serialize_when_none=False)
    reference = ModelType(ReferenceModel)
