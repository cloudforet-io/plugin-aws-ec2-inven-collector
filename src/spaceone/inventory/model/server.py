from schematics import Model
from schematics.types import serializable, ModelType, ListType, StringType
from spaceone.inventory.model import OS, AWS, Hardware, SecurityGroupRule, Compute, LoadBalancer, VPC, Subnet, \
    AutoScalingGroup, NIC, Disk, ServerMetadata


class ReferenceModel(Model):
    class Option:
        serialize_when_none = False

    resource_id = StringType(required=False, serialize_when_none=False)
    external_link = StringType(required=False, serialize_when_none=False)


class ServerData(Model):
    os = ModelType(OS)
    aws = ModelType(AWS)
    hardware = ModelType(Hardware)
    security_group_rules = ListType(ModelType(SecurityGroupRule))
    public_ip_address = StringType()
    compute = ModelType(Compute)
    public_dns = StringType()
    load_balancers = ListType(ModelType(LoadBalancer))
    vpc = ModelType(VPC)
    subnet = ModelType(Subnet)
    auto_scaling_group = ModelType(AutoScalingGroup, serialize_when_none=False)

    @serializable
    def cloudwatch(self):
        return {
            "namespace": "AWS/EC2",
            "dimensions": [
                {
                    "Name": "InstanceId",
                    "Value": self.compute.instance_id
                }
            ],
            "region_name": self.compute.region_name
        }


class Server(Model):
    name = StringType()
    data = ModelType(ServerData)
    nics = ListType(ModelType(NIC))
    disks = ListType(ModelType(Disk))
    ip_addresses = ListType(StringType())
    server_type = StringType(default='VM')
    os_type = StringType(choices=('LINUX', 'WINDOWS'))
    provider = StringType(default='aws')
    _metadata = ModelType(ServerMetadata, serialized_name='metadata')
    # reference = ModelType(ReferenceModel)

    @serializable
    def reference(self):
        return {
            "resource_id": f"arn:aws:ec2:{self.data.compute.region_name}:{self.data.compute.account_id}:instance/{self.data.compute.instance_id}",
            "external_link": f"https://{self.data.compute.region_name}.console.aws.amazon.com/ec2/v2/home?region={self.data.compute.region_name}#Instances:instanceId={self.data.compute.instance_id}"
        }

