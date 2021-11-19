from schematics import Model
from schematics.types import ModelType, ListType, StringType, PolyModelType, DateTimeType
from spaceone.inventory.model import OS, AWS, Hardware, SecurityGroup, Compute, LoadBalancer, VPC, Subnet, \
    AutoScalingGroup, NIC, Disk, ServerMetadata, CloudWatch


class ReferenceModel(Model):
    class Option:
        serialize_when_none = False

    resource_id = StringType(required=False, serialize_when_none=False)
    external_link = StringType(required=False, serialize_when_none=False)


class Tags(Model):
    key = StringType(deserialize_from="Key")
    value = StringType(deserialize_from="Value")


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
    cloudwatch = ModelType(CloudWatch)


class Server(Model):
    name = StringType(default='')
    region_code = StringType()
    data = ModelType(ServerData)
    tags = ListType(ModelType(Tags))
    nics = ListType(ModelType(NIC))
    disks = ListType(ModelType(Disk))
    primary_ip_address = StringType(default='')
    ip_addresses = ListType(StringType())
    account = StringType()
    type = StringType(serialize_when_none=False)
    size = StringType(serialize_when_none=False)
    launched_at = DateTimeType(serialize_when_none=False)
    server_type = StringType(default='VM')
    os_type = StringType(choices=('LINUX', 'WINDOWS'))
    provider = StringType(default='aws')
    cloud_service_type = StringType(default='Instance')
    cloud_service_group = StringType(default='EC2')
    _metadata = PolyModelType(ServerMetadata, serialized_name='metadata', serialize_when_none=False)
    reference = ModelType(ReferenceModel)
