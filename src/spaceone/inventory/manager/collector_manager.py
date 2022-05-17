__all__ = ['CollectorManager']

import time
import json
import logging
from spaceone.core.manager import BaseManager
from spaceone.inventory.connector import EC2Connector
from spaceone.inventory.manager.ec2 import EC2InstanceManager, AutoScalingGroupManager, LoadBalancerManager, \
    DiskManager, NICManager, VPCManager, SecurityGroupManager, CloudWatchManager
from spaceone.inventory.manager.metadata.metadata_manager import MetadataManager
from spaceone.inventory.model.server import Server, ReferenceModel
from spaceone.inventory.model.region import Region
from spaceone.inventory.model.cloud_service_type import CloudServiceType
from spaceone.inventory.model.resource import ErrorResourceResponse, ServerResourceResponse
from spaceone.inventory.model.metadata.metadata import CloudServiceTypeMetadata
from spaceone.inventory.model.metadata.metadata_dynamic_field import TextDyField, EnumDyField, SizeField, DateTimeDyField, ListDyField
from spaceone.inventory.conf.cloud_service_conf import *


_LOGGER = logging.getLogger(__name__)


class CollectorManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)

    def verify(self, secret_data, region_name):
        """ Check connection
        """
        ec2_connector = self.locator.get_connector('EC2Connector')
        r = ec2_connector.verify(secret_data, region_name)
        # ACTIVE/UNKNOWN
        return r

    def list_regions(self, secret_data, region_name):
        ec2_connector: EC2Connector = self.locator.get_connector('EC2Connector')
        ec2_connector.set_client(secret_data, region_name)

        return ec2_connector.list_regions()

    def list_instances(self, params):
        servers = []
        errors = []

        ec2_connector: EC2Connector = self.locator.get_connector('EC2Connector')
        ec2_connector.set_client(params['secret_data'], params['region_name'])

        instance_filter = {}
        # Instance list and account ID
        if 'instance_ids' in params and len(params['instance_ids']) > 0:
            instance_filter.update({'Filters': [{'Name': 'instance-id', 'Values': params['instance_ids']}]})

        instances, account_id = ec2_connector.list_instances(**instance_filter)

        _LOGGER.debug(f'[list_instances] [{params["region_name"]}] INSTANCE COUNT : {len(instances)}')

        if instances:
            ins_manager: EC2InstanceManager = EC2InstanceManager(params, ec2_connector=ec2_connector)
            asg_manager: AutoScalingGroupManager = AutoScalingGroupManager(params)
            elb_manager: LoadBalancerManager = LoadBalancerManager(params, ec2_connector=ec2_connector)
            disk_manager: DiskManager = DiskManager(params)
            nic_manager: NICManager = NICManager(params)
            vpc_manager: VPCManager = VPCManager(params)
            sg_manager: SecurityGroupManager = SecurityGroupManager(params)
            cw_manager: CloudWatchManager = CloudWatchManager(params)

            meta_manager: MetadataManager = MetadataManager()

            # Instance Type
            itypes = ec2_connector.list_instance_types()

            # Image
            images = ec2_connector.list_images(ImageIds=self.get_image_ids(instances))

            # Auto Scaling group list
            auto_scaling_groups = ec2_connector.list_auto_scaling_groups()
            launch_configurations = ec2_connector.list_launch_configurations()

            # LB list
            load_balancers = ec2_connector.list_load_balancers()
            elb_manager.set_listeners_into_load_balancers(load_balancers)

            target_groups = ec2_connector.list_target_groups()

            for target_group in target_groups:
                target_healths = ec2_connector.list_target_health(target_group.get('TargetGroupArn'))
                target_group['target_healths'] = target_healths

            # VPC
            vpcs = ec2_connector.list_vpcs()
            subnets = ec2_connector.list_subnets()

            # Volume
            volumes = ec2_connector.list_volumes()

            # IP
            eips = ec2_connector.list_elastic_ips()

            # Security Group
            sgs = ec2_connector.list_security_groups()

            for instance in instances:
                try:
                    instance_id = instance.get('InstanceId')
                    instance_ip = instance.get('PrivateIpAddress')

                    server_data = ins_manager.get_server_info(instance, itypes, images)
                    auto_scaling_group_vo = asg_manager.get_auto_scaling_info(instance_id, auto_scaling_groups,
                                                                              launch_configurations)

                    load_balancer_vos = elb_manager.get_load_balancer_info(load_balancers, target_groups,
                                                                           instance_id, instance_ip)

                    disk_vos = disk_manager.get_disk_info(self.get_volume_ids(instance), volumes)
                    vpc_vo, subnet_vo = vpc_manager.get_vpc_info(instance.get('VpcId'), instance.get('SubnetId'),
                                                                 vpcs, subnets, params['region_name'])

                    nic_vos = nic_manager.get_nic_info(instance.get('NetworkInterfaces'), subnet_vo)

                    sg_ids = [security_group.get('GroupId') for security_group in instance.get('SecurityGroups', []) if
                              security_group.get('GroupId') is not None]
                    sg_rules_vos = sg_manager.get_security_group_info(sg_ids, sgs)
                    cloudwatch_vo = cw_manager.get_cloudwatch_info(instance_id, params['region_name'])

                    server_data.update({
                        'region_code': params.get("region_name", ''),
                        'tags': instance.get('Tags', [])
                    })

                    server_data['data'].update({
                        'primary_ip_address': instance_ip,
                        'nics': nic_vos,
                        'disks': disk_vos,
                        'load_balancer': load_balancer_vos,
                        'security_group': sg_rules_vos,
                        'vpc': vpc_vo,
                        'subnet': subnet_vo,
                        'cloudwatch': cloudwatch_vo
                    })

                    if auto_scaling_group_vo:
                        server_data['data'].update({
                            'auto_scaling_group': auto_scaling_group_vo
                        })

                    # IP addr : ip_addresses = nics.ip_addresses + data.public_ip_address
                    server_data.update({
                        'ip_addresses': self.merge_ip_addresses(server_data),
                    })

                    server_data['data']['compute']['account'] = account_id
                    server_data['account'] = account_id

                    server_data.update({
                        '_metadata': meta_manager.get_metadata(),
                        'reference': ReferenceModel({
                            'resource_id': server_data['data']['compute']['instance_id'],
                            'external_link': f"https://{params.get('region_name')}.console.aws.amazon.com/ec2/v2/home?region={params.get('region_name')}#Instances:instanceId={server_data['data']['compute']['instance_id']}"
                        })
                    })

                    server_resource = Server(server_data, strict=False)
                    servers.append(ServerResourceResponse({'resource': server_resource}))

                except Exception as e:
                    _LOGGER.error(f'[list_instances] [{instance.get("InstanceId")}] {e}')

                    if type(e) is dict:
                        error_resource_response = ErrorResourceResponse({'message': json.dumps(e)})
                    else:
                        error_resource_response = ErrorResourceResponse(
                            {'message': str(e), 'resource': {'resource_id': instance.get('InstanceId')}})

                    errors.append(error_resource_response)

        return servers, errors

    def list_resources(self, params):
        start_time = time.time()
        total_resources = []

        try:
            resources, error_resources = self.list_instances(params)
            total_resources.extend(resources)
            total_resources.extend(error_resources)
            _LOGGER.debug(f'[list_resources] [{params["region_name"]}] Finished {time.time() - start_time} Seconds')

            return total_resources

        except Exception as e:
            _LOGGER.error(f'[list_resources] [{params["region_name"]}] {e}')

            if type(e) is dict:
                error_resource_response = ErrorResourceResponse({'message': json.dumps(e)})
            else:
                error_resource_response = ErrorResourceResponse({'message': str(e)})

            total_resources.append(error_resource_response)
            return total_resources

    @staticmethod
    def list_cloud_service_types():
        metadata = CloudServiceTypeMetadata.set_meta(
            fields=[
                TextDyField.data_source('Server ID', 'server_id'),
                TextDyField.data_source('Name', 'name'),
                TextDyField.data_source('Resource ID', 'reference.resource_id'),
                EnumDyField.data_source('Management State', 'state', default_state={
                    'safe': ['ACTIVE'], 'disable': ['DELETED']
                }, options={'is_optional': True}),
                TextDyField.data_source('Instance Type', 'data.compute.instance_type'),
                TextDyField.data_source('Core', 'data.hardware.core'),
                TextDyField.data_source('Memory', 'data.hardware.memory'),
                TextDyField.data_source('Provider', 'provider', reference={
                    'resource_type': 'identity.Provider',
                    'reference_key': 'provider'
                }),
                TextDyField.data_source('Cloud Service Group', 'cloud_service_group', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Cloud Service Type', 'cloud_service_type', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Instance ID', 'data.compute.instance_id', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Key Pair', 'data.compute.keypair', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Image', 'data.compute.image', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Image', 'data.compute.image', options={
                    'is_optional': True
                }),
                EnumDyField.data_source('Instance State', 'data.compute.instance_state', default_state={
                    'safe': ['RUNNING'],
                    'warning': ['PENDING', 'REBOOTING', 'SHUTTING-DOWN', 'STOPPING', 'STARTING',
                                'PROVISIONING', 'STAGING', 'DEALLOCATING', 'REPAIRING'],
                    'alert': ['STOPPED', 'DEALLOCATED', 'SUSPENDED'],
                    'disable': ['TERMINATED']
                }, options={'is_optional': True}),
                TextDyField.data_source('Availability Zone', 'data.compute.az'),
                TextDyField.data_source('OS Type', 'data.os.os_type', options={
                    'is_optional': True
                }),
                TextDyField.data_source('OS', 'data.os.os_distro'),
                TextDyField.data_source('OS Architecture', 'data.os.os_arch', options={
                    'is_optional': True
                }),
                TextDyField.data_source('Primary IP', 'data.primary_ip_address'),
                TextDyField.data_source('Public IP', 'data.nics.public_ip_address'),
                TextDyField.data_source('Public DNS', 'data.tags.public_dns', options={
                    'is_optional': True
                }),
                TextDyField.data_source('All IP', 'ip_addresses', options={
                    'is_optional': True
                }),
                TextDyField.data_source('MAC Address', 'nics.mac_address', options={
                    'is_optional': True
                }),
                TextDyField.data_source('CIDR', 'nics.cidr', options={
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
                TextDyField.data_source('ELB Name', 'data.load_balancers.name', options={
                    'is_optional': True
                }),
                TextDyField.data_source('ELB DNS', 'data.load_balancers.dns', options={
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
                TextDyField.data_source('Account ID', 'account'),
                TextDyField.data_source('Region', 'region_code',
                                        options={'is_optional': True},
                                        reference={'resource_type': 'inventory.Region',
                                                   'reference_key': 'region_code'}),
                TextDyField.data_source('Project', 'project_id',
                                        options={'sortable': False},
                                        reference={'resource_type': 'inventory.Project',
                                                   'reference_key': 'project_id'}),
                TextDyField.data_source('Service Accounts', 'collection_info.service_accounts',
                                        options={'is_optional': True},
                                        reference={'resource_type': 'inventory.ServiceAccount',
                                                   'reference_key': 'service_account_id'}),
                TextDyField.data_source('Secrets', 'collection_info.secrets',
                                        options={'is_optional': True},
                                        reference={'resource_type': 'secret.Secret',
                                                   'reference_key': 'secret_id'}),
                TextDyField.data_source('Collectors', 'collection_info.collectors',
                                        options={'is_optional': True},
                                        reference={'resource_type': 'inventory.Collector',
                                                   'reference_key': 'collector_id'}),
                TextDyField.data_source('Launched', 'launched_at', options={'is_optional': True}),
                DateTimeDyField.data_source('Last Collected', 'updated_at', options={'source_type': "iso8601"}),
                DateTimeDyField.data_source('Created', 'created_at', options={
                    'source_type': "iso8601",
                    'is_optional': True
                }),
                DateTimeDyField.data_source('Deleted', 'deleted_at', options={
                    'source_type': "iso8601",
                    'is_optional': True
                })
            ]
        )

        cloud_service_type = {
            '_metadata': metadata,
            'tags': {
                'spaceone:icon': 'https://spaceone-custom-assets.s3.ap-northeast-2.amazonaws.com/console-assets/icons/aws-ec2.svg',
            }
        }
        return [CloudServiceType(cloud_service_type, strict=False)]

    @staticmethod
    def get_volume_ids(instance):
        block_device_mappings = instance.get('BlockDeviceMappings', [])
        return [block_device_mapping['Ebs']['VolumeId'] for block_device_mapping in block_device_mappings if block_device_mapping.get('Ebs') is not None]

    @staticmethod
    def get_image_ids(instances):
        image_ids = [instance.get('ImageId') for instance in instances if instance.get('ImageId') is not None]
        return list(set(image_ids))

    @staticmethod
    def merge_ip_addresses(server_data):
        nics = server_data.get('data', {}).get('nics', [])

        nic_ip_addresses = []
        for nic in nics:
            nic_ip_addresses.extend(nic.ip_addresses)

        merge_ip_address = nic_ip_addresses

        return list(set(merge_ip_address))

    @staticmethod
    def get_region_from_result(resource):
        match_region_info = REGION_INFO.get(getattr(resource, 'region_code', None))

        if match_region_info is not None:
            region_info = match_region_info.copy()
            region_info.update({
                'region_code': resource.region_code
            })

            return Region(region_info, strict=False)

        return None
