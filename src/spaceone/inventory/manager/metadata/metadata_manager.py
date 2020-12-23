from spaceone.core.manager import BaseManager
from spaceone.inventory.model.metadata.metadata import ServerMetadata
from spaceone.inventory.model.metadata.metadata_dynamic_layout import ItemDynamicLayout, TableDynamicLayout, \
    ListDynamicLayout
from spaceone.inventory.model.metadata.metadata_dynamic_field import TextDyField, EnumDyField, ListDyField, \
    DateTimeDyField, SizeField

ec2_instance = ItemDynamicLayout.set_fields('EC2 Instance', fields=[
    TextDyField.data_source('Instance ID', 'data.compute.instance_id'),
    EnumDyField.data_source('Instance State', 'data.compute.instance_state', default_state={
        'safe': ['RUNNING'],
        'warning': ['PENDING', 'STOPPING'],
        'disable': ['SHUTTING-DOWN'],
        'alert': ['STOPPED']
    }),
    TextDyField.data_source('Instance Type', 'data.compute.instance_type'),
    EnumDyField.data_source('EC2 Lifecycle', 'data.aws.lifecycle', default_badge={
        'indigo.500': ['spot'], 'coral.600': ['scheduled']
    }),
    TextDyField.data_source('Key Pair', 'data.compute.keypair'),
    TextDyField.data_source('IAM Role ARN', 'data.aws.iam_instance_profile.arn'),
    EnumDyField.data_source('EBS-Optimized', 'data.aws.ebs_optimized', default_badge={
        'indigo.500': ['true'], 'coral.600': ['false']
    }),
    TextDyField.data_source('AMI ID', 'data.compute.image'),
    TextDyField.data_source('Region', 'region_code'),
    TextDyField.data_source('Availability Zone', 'data.compute.az'),
    EnumDyField.data_source('Termination Protection', 'data.aws.termination_protection', default_badge={
        'indigo.500': ['true'], 'coral.600': ['false']
    }),
    ListDyField.data_source('Public DNS', 'nics',
                            default_badge={'type': 'outline', 'sub_key': 'tags.public_dns'}),
    ListDyField.data_source('Public IP', 'nics',
                            default_badge={'type': 'outline', 'sub_key': 'public_ip_address'}),
    ListDyField.data_source('Security Groups', 'data.compute.security_groups',
                            default_badge={'type': 'outline', 'delimiter': '<br>', 'sub_key': 'display'},
                            reference={
                                'resource_type': 'inventory.CloudService',
                                'reference_key': 'data.group_id'
                            }),
    TextDyField.data_source('Account ID', 'data.compute.account'),
    DateTimeDyField.data_source('Launched At', 'data.compute.launched_at'),
])

ec2_vpc = ItemDynamicLayout.set_fields('VPC', fields=[
    TextDyField.data_source('VPC ID', 'data.vpc.vpc_id', reference={
        'resource_type': 'inventory.CloudService',
        'reference_key': 'data.vpc_id'
    }),
    TextDyField.data_source('VPC Name', 'data.vpc.vpc_name'),
    TextDyField.data_source('Subnet ID', 'data.subnet.subnet_id', reference={
        'resource_type': 'inventory.CloudService',
        'reference_key': 'data.subnet_id'
    }),
    TextDyField.data_source('Subnet Name', 'data.subnet.subnet_name'),
])

ec2_asg = ItemDynamicLayout.set_fields('Auto Scaling Group', fields=[
    TextDyField.data_source('Auto Scaling Group', 'data.auto_scaling_group.name', reference={
        'resource_type': 'inventory.CloudService',
        'reference_key': 'data.auto_scaling_group_name'
    }),
    TextDyField.data_source('Launch Configuration', 'data.auto_scaling_group.launch_configuration.name', reference={
        'resource_type': 'inventory.CloudService',
        'reference_key': 'data.launch_configuration_name'
    }),
    TextDyField.data_source('Launch Template', 'data.auto_scaling_group.launch_template.name', reference={
        'resource_type': 'inventory.CloudService',
        'reference_key': 'data.launch_template_name'
    }),
])

ec2 = ListDynamicLayout.set_layouts('AWS EC2', layouts=[ec2_instance, ec2_vpc, ec2_asg])

disk = TableDynamicLayout.set_fields('Disk', root_path='disks', fields=[
    TextDyField.data_source('Index', 'device_index'),
    TextDyField.data_source('Name', 'device'),
    SizeField.data_source('Size(GB)', 'size', options={
        'display_unit': 'GB',
        'source_unit': 'GB'
    }),
    TextDyField.data_source('Volume ID', 'tags.volume_id'),
    EnumDyField.data_source('Volume Type', 'tags.volume_type',
                            default_outline_badge=['gp2', 'gp3', 'io1', 'sc1', 'st1', 'standard']),
    TextDyField.data_source('IOPS', 'tags.iops'),
    EnumDyField.data_source('Encrypted', 'tags.encrypted', default_badge={
        'indigo.500': ['true'], 'coral.600': ['false']
    }),
])

nic = TableDynamicLayout.set_fields('NIC', root_path='nics', fields=[
    TextDyField.data_source('Index', 'device_index'),
    TextDyField.data_source('MAC Address', 'mac_address'),
    ListDyField.data_source('IP Addresses', 'ip_addresses', options={'delimiter': '<br>'}),
    TextDyField.data_source('CIDR', 'cidr'),
    TextDyField.data_source('Public IP', 'public_ip_address'),
    TextDyField.data_source('Public DNS', 'tags.public_dns')
])

security_group = TableDynamicLayout.set_fields('Security Groups', root_path='data.security_group', fields=[
    EnumDyField.data_source('Direction', 'direction', default_badge={
        'indigo.500': ['inbound'], 'coral.600': ['outbound']
    }),
    TextDyField.data_source('Name', 'security_group_name', reference={
        'resource_type': 'inventory.CloudService',
        'reference_key': 'data.group_name'
    }),
    EnumDyField.data_source('Protocol', 'protocol', default_outline_badge=['ALL', 'TCP', 'UDP', 'ICMP']),
    TextDyField.data_source('Port Rage', 'port'),
    TextDyField.data_source('Remote', 'remote'),
    TextDyField.data_source('Description', 'description'),
])

elb = TableDynamicLayout.set_fields('ELB', root_path='data.load_balancer', fields=[
    TextDyField.data_source('Name', 'name', reference={
        'resource_type': 'inventory.CloudService',
        'reference_key': 'data.load_balancer_name'
    }),
    TextDyField.data_source('Endpoint', 'endpoint', reference={
        'resource_type': 'inventory.CloudService',
        'reference_key': 'data.dns_name'
    }),
    EnumDyField.data_source('Type', 'type', default_badge={
        'indigo.500': ['network'], 'coral.600': ['application']
    }),
    ListDyField.data_source('Protocol', 'protocol', options={'delimiter': '<br>'}),
    ListDyField.data_source('Port', 'port', options={'delimiter': '<br>'}),
    EnumDyField.data_source('Scheme', 'scheme', default_badge={
        'indigo.500': ['internet-facing'], 'coral.600': ['internal']
    }),
])

tags = TableDynamicLayout.set_fields('AWS Tags', root_path='data.aws.tags', fields=[
    TextDyField.data_source('Key', 'key'),
    TextDyField.data_source('Value', 'value'),
])

metadata = ServerMetadata.set_layouts([ec2, tags, disk, nic, security_group, elb])


class MetadataManager(BaseManager):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metadata = metadata

    def get_metadata(self):
        return self.metadata
