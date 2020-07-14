from schematics import Model
from schematics.types import ModelType, StringType, serializable, ListType
from spaceone.inventory.model import *


class ServerData(Model):
    os = ModelType(OS)
    aws = ModelType(AWS)
    hardware = ModelType(Hardware)
    security_group_rules = ListType(ModelType(SecurityGroupRule))
    public_ip_address = StringType()
    load_balancers = ListType(ModelType(LoadBalancer))
    vpc = ModelType(VPC)
    auto_scaling_group = ModelType(AutoScalingGroup)
    compute = ModelType(Compute)
    subnet = ModelType(Subnet)
    public_dns = StringType()


class Server(Model):
    data = ModelType(ServerData)
    nics = ListType(ModelType(NIC))
    disks = ListType(ModelType(Disk))
    ip_addresses = ListType(StringType())
    server_type = StringType(default='VM')
    os_type =  StringType(choices=('LINUX', 'WINDOWS'))
    provider = StringType(default='aws')
    _metadata = ModelType(ServerMetadata, serialized_name='metadata')

    @serializable
    def reference(self):
        return {
            "resource_id": f"arn:aws:ec2:{self.data.compute.region_name}:{self.data.compute.account_id}:instance/{self.data.compute.instance_id}",
            "external_link": f"https://{self.data.compute.region_name}.console.aws.amazon.com/ec2/v2/home?region={self.compute.region_name}#Instances:instanceId={self.data.compute.instance_id}"
        }
