import os
from spaceone.core.manager import BaseManager
from spaceone.inventory.libs.utils import *
from spaceone.inventory.model.metadata.metadata import ServerMetadata, CloudServiceTypeMetadata
from spaceone.inventory.model.metadata.metadata_dynamic_layout import ItemDynamicLayout, TableDynamicLayout, \
    ListDynamicLayout
from spaceone.inventory.model.metadata.metadata_dynamic_field import TextDyField, EnumDyField, ListDyField, \
    DateTimeDyField, SizeField, SearchField
from spaceone.inventory.model.metadata.metadata_dynamic_widget import CardWidget, ChartWidget

current_dir = os.path.abspath(os.path.dirname(__file__))

total_count_conf = os.path.join(current_dir, 'widget/total_running_count.yaml')
total_disk_size_conf = os.path.join(current_dir, 'widget/total_disk_size.yaml')
total_memory_size_conf = os.path.join(current_dir, 'widget/total_memory_size.yaml')
total_vcpu_count_conf = os.path.join(current_dir, 'widget/total_vcpu_count.yaml')
count_by_account_conf = os.path.join(current_dir, 'widget/count_by_account.yaml')
count_by_instance_type_conf = os.path.join(current_dir, 'widget/count_by_instance_type.yaml')
count_by_region_conf = os.path.join(current_dir, 'widget/count_by_region.yaml')


class MetadataManager(BaseManager):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_cloud_service_type_metadata():
        metadata = CloudServiceTypeMetadata.set_meta(
            fields=[
                EnumDyField.data_source('Instance State', 'data.compute.instance_state', default_state={
                    'safe': ['RUNNING'],
                    'warning': ['PENDING', 'REBOOTING', 'SHUTTING-DOWN', 'STOPPING', 'STARTING',
                                'PROVISIONING', 'STAGING', 'DEALLOCATING', 'REPAIRING'],
                    'alert': ['STOPPED', 'DEALLOCATED', 'SUSPENDED'],
                    'disable': ['TERMINATED']
                }),
                TextDyField.data_source('Instance Type', 'data.compute.instance_type'),
                TextDyField.data_source('Core', 'data.hardware.core'),
                TextDyField.data_source('Memory', 'data.hardware.memory'),
                TextDyField.data_source('Instance ID', 'data.compute.instance_id', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Root Volume Type', 'data.aws.root_volume_type', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Key Pair', 'data.compute.keypair', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Image', 'data.compute.image', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Availability Zone', 'data.compute.az'),
                TextDyField.data_source('Termination Protection', 'data.aws.termination_protection', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Auto Recovery', 'data.aws.auto_recovery', options={
                    'is_optional': True
                }),
                TextDyField.data_source('OS Type', 'data.os.os_type', options={
                    'is_optional': True
                }),
                TextDyField.data_source('OS', 'data.os.os_distro'),
                TextDyField.data_source('OS Architecture', 'data.os.os_arch', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Primary IP', 'data.primary_ip_address'),
                ListDyField.data_source('Public DNS', 'data.nics', options={
                    'sub_key': 'tags.public_dns',
                    'is_optional': True
                }),
                ListDyField.data_source('Public IP', 'data.nics', options={
                    'sub_key': 'public_ip_address',
                    'is_optional': True
                }),
                TextDyField.data_source('All IP', 'ip_addresses', options={
                    'is_optional': True
                }),
                TextDyField.data_source('MAC Address', 'data.nics.mac_address', options={
                    'is_optional': True
                }),
                TextDyField.data_source('CIDR', 'data.nics.cidr', options={
                    'is_optional': True
                }),
                TextDyField.data_source('VPC ID', 'data.vpc.vpc_id', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Subnet ID', 'data.subnet.subnet_id', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Subnet Name', 'data.subnet.subnet_name', options={
                    'is_optional': True
                }),
                TextDyField.data_source('ELB Name', 'data.load_balancer.name', options={
                    'is_optional': True
                }),
                TextDyField.data_source('IAM Role ARN', 'data.aws.iam_instance_profile.arn', options={
                    'is_optional': True
                }),
                TextDyField.data_source('EC2 Lifecycle', 'data.aws.lifecycle', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Auto Scaling Group', 'data.auto_scaling_group.name', options={
                    'is_optional': True
                }),
                TextDyField.data_source('CPU Utilization', 'data.monitoring.cpu.utilization.avg', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Average)'
                }),
                TextDyField.data_source('Memory Usage', 'data.monitoring.memory.usage.avg', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Average)'
                }),
                TextDyField.data_source('Disk Read IOPS', 'data.monitoring.disk.read_iops.avg', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Average)'
                }),
                TextDyField.data_source('Disk Write IOPS', 'data.monitoring.disk.write_iops.avg', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Average)'
                }),
                SizeField.data_source('Disk Read Throughput', 'data.monitoring.disk.read_throughput.avg', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Average)'
                }),
                SizeField.data_source('Disk Write Throughput', 'data.monitoring.disk.write_throughput.avg', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Average)'
                }),
                TextDyField.data_source('Network Received PPS', 'data.monitoring.network.received_pps.avg', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Average)'
                }),
                TextDyField.data_source('Network Send PPS', 'data.monitoring.network.sent_pps.avg', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Average)'
                }),
                SizeField.data_source('Network Received Throughput', 'data.monitoring.network.received_throughput.avg',
                                      options={
                                          'default': 0,
                                          'is_optional': True,
                                          'field_description': '(Daily Average)'
                                      }),
                SizeField.data_source('Network Sent Throughput', 'data.monitoring.network.sent_throughput.avg',
                                      options={
                                          'default': 0,
                                          'is_optional': True,
                                          'field_description': '(Daily Average)'
                                      }),
                TextDyField.data_source('CPU Utilization', 'data.monitoring.cpu.utilization.max', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Max)'
                }),
                TextDyField.data_source('Memory Usage', 'data.monitoring.memory.usage.max', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Max)'
                }),
                TextDyField.data_source('Disk Read IOPS', 'data.monitoring.disk.read_iops.max', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Max)'
                }),
                TextDyField.data_source('Disk Write IOPS', 'data.monitoring.disk.write_iops.max', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Max)'
                }),
                SizeField.data_source('Disk Read Throughput', 'data.monitoring.disk.read_throughput.max', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Max)'
                }),
                SizeField.data_source('Disk Write Throughput', 'data.monitoring.disk.write_throughput.max', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Max)'
                }),
                TextDyField.data_source('Network Received PPS', 'data.monitoring.network.received_pps.max', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Max)'
                }),
                TextDyField.data_source('Network Send PPS', 'data.monitoring.network.sent_pps.max', options={
                    'default': 0,
                    'is_optional': True,
                    'field_description': '(Daily Max)'
                }),
                SizeField.data_source('Network Received Throughput', 'data.monitoring.network.received_throughput.max',
                                      options={
                                          'default': 0,
                                          'is_optional': True,
                                          'field_description': '(Daily Max)'
                                      }),
                SizeField.data_source('Network Sent Throughput', 'data.monitoring.network.sent_throughput.max',
                                      options={
                                          'default': 0,
                                          'is_optional': True,
                                          'field_description': '(Daily Max)'
                                      }),
                TextDyField.data_source('Account ID', 'account')
            ],
            search=[
                SearchField.set(name='IP Address', key='ip_addresses'),
                SearchField.set(name='Instance ID', key='data.compute.instance_id'),
                SearchField.set(name='Instance State', key='data.compute.instance_state'),
                SearchField.set(name='Instance Type', key='data.compute.instance_type'),
                SearchField.set(name='Key Pair', key='data.compute.keypair'),
                SearchField.set(name='Image', key='data.compute.image'),
                SearchField.set(name='Availability Zone', key='data.compute.az'),
                SearchField.set(name='OS Type', key='data.os.os_type'),
                SearchField.set(name='OS Architecture', key='data.os.os_arch'),
                SearchField.set(name='Termination Protection', key='data.aws.termination_protection', data_type='boolean'),
                SearchField.set(name='Auto Recovery', key='data.aws.auto_recovery'),
                SearchField.set(name='Root Volume Type', key='data.aws.root_volume_type'),
                SearchField.set(name='MAC Address', key='data.nics.mac_address'),
                SearchField.set(name='Public IP Address', key='data.nics.public_ip_address'),
                SearchField.set(name='Public DNS', key='data.nics.tags.public_dns'),
                SearchField.set(name='VPC ID', key='data.vpc.vpc_id'),
                SearchField.set(name='VPC Name', key='data.vpc.vpc_name'),
                SearchField.set(name='Subnet ID', key='data.subnet.subnet_id'),
                SearchField.set(name='Subnet Name', key='data.subnet.subnet_name'),
                SearchField.set(name='ELB Name', key='data.load_balancer.name'),
                SearchField.set(name='ELB DNS', key='data.load_balancer.endpoint'),
                SearchField.set(name='Auto Scaling Group', key='data.auto_scaling_group.name'),
                SearchField.set(name='Core', key='data.hardware.core', data_type='integer'),
                SearchField.set(name='Memory', key='data.hardware.memory', data_type='float'),
                SearchField.set(name='Provider', key='provider', reference='identity.Provider'),
                SearchField.set(name='Account ID', key='account'),
                SearchField.set(name='Cloud Service Group', key='cloud_service_group'),
                SearchField.set(name='Cloud Service Type', key='cloud_service_type'),
                SearchField.set(name='Last Collected', key='updated_at', data_type='datetime'),
            ],
            widget=[
                CardWidget.set(**get_data_from_yaml(total_count_conf)),
                CardWidget.set(**get_data_from_yaml(total_vcpu_count_conf)),
                CardWidget.set(**get_data_from_yaml(total_memory_size_conf)),
                CardWidget.set(**get_data_from_yaml(total_disk_size_conf)),
                ChartWidget.set(**get_data_from_yaml(count_by_region_conf)),
                ChartWidget.set(**get_data_from_yaml(count_by_instance_type_conf)),
                ChartWidget.set(**get_data_from_yaml(count_by_account_conf)),
            ]
        )
        return metadata

    @staticmethod
    def get_server_metadata():
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
            TextDyField.data_source('Root Volume Type', 'data.aws.root_volume_type'),
            TextDyField.data_source('Termination Protection', 'data.aws.termination_protection'),
            TextDyField.data_source('Auto-Recovery Behavior', 'data.aws.auto_recovery'),
            TextDyField.data_source('AMI ID', 'data.compute.image'),
            TextDyField.data_source('Region', 'region_code'),
            TextDyField.data_source('Availability Zone', 'data.compute.az'),
            EnumDyField.data_source('Termination Protection', 'data.aws.termination_protection', default_badge={
                'indigo.500': ['true'], 'coral.600': ['false']
            }),
            ListDyField.data_source('Public DNS', 'data.nics', options={
                'sub_key': 'tags.public_dns'
            }),
            ListDyField.data_source('Public IP', 'data.nics', options={
                'sub_key': 'public_ip_address'
            }),
            ListDyField.data_source('Security Groups', 'data.compute.security_groups', options={
                'delimiter': '<br>', 'sub_key': 'display'
            }, reference={
                'resource_type': 'inventory.CloudService',
                'reference_key': 'data.group_id'
            }),
            TextDyField.data_source('Account ID', 'data.compute.account'),
            DateTimeDyField.data_source('Launched At', 'data.compute.launched_at'),
        ])

        ec2_os = ItemDynamicLayout.set_fields('Operating System', fields=[
            TextDyField.data_source('OS Type', 'data.os.os_type', options={
                'translation_id': 'PAGE_SCHEMA.OS_TYPE'
            }),
            TextDyField.data_source('OS Distribution', 'data.os.os_distro', options={
                'translation_id': 'PAGE_SCHEMA.OS_DISTRO',
            }),
            TextDyField.data_source('OS Architecture', 'data.os.os_arch', options={
                'translation_id': 'PAGE_SCHEMA.OS_ARCH',
            })
        ])

        ec2_hw = ItemDynamicLayout.set_fields('Hardware', fields=[
            TextDyField.data_source('Core', 'data.hardware.core', options={
                'translation_id': 'PAGE_SCHEMA.CPU_CORE',
            }),
            TextDyField.data_source('Memory', 'data.hardware.memory', options={
                'translation_id': 'PAGE_SCHEMA.MEMORY',
            }),
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
            TextDyField.data_source('Launch Configuration', 'data.auto_scaling_group.launch_configuration.name',
                                    reference={
                                        'resource_type': 'inventory.CloudService',
                                        'reference_key': 'data.launch_configuration_name'
                                    }),
            TextDyField.data_source('Launch Template', 'data.auto_scaling_group.launch_template.name', reference={
                'resource_type': 'inventory.CloudService',
                'reference_key': 'data.launch_template_name'
            }),
        ])

        ec2 = ListDynamicLayout.set_layouts('AWS EC2', layouts=[ec2_instance, ec2_os, ec2_hw, ec2_vpc, ec2_asg])

        disk = TableDynamicLayout.set_fields('Disk', root_path='data.disks', fields=[
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

        nic = TableDynamicLayout.set_fields('NIC', root_path='data.nics', fields=[
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
            TextDyField.data_source('SG ID', 'security_group_id', reference={
                'resource_type': 'inventory.CloudService',
                'reference_key': 'reference.resource_id'
            }),
            TextDyField.data_source('Name', 'security_group_name'),
            EnumDyField.data_source('Protocol', 'protocol', default_outline_badge=['ALL', 'TCP', 'UDP', 'ICMP']),
            TextDyField.data_source('Port Range', 'port'),
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

        return ServerMetadata.set_layouts([ec2, disk, nic, security_group, elb])
