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
from spaceone.inventory.model.cloudtrail import CloudTrail
from spaceone.inventory.model.cloud_service_type import CloudServiceType
from spaceone.inventory.model.resource import ErrorResourceResponse, ServerResourceResponse
from spaceone.inventory.conf.cloud_service_conf import *
from spaceone.inventory.libs.utils import convert_tags


_LOGGER = logging.getLogger(__name__)


class CollectorManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        meta_manager: MetadataManager = MetadataManager()
        region_name = params.get("region_name", '')
        cloudtrail_resource_type = 'AWS::EC2::Instance'

        instance_filter = {}
        # Instance list and account ID
        if 'instance_ids' in params and len(params['instance_ids']) > 0:
            instance_filter.update({'Filters': [{'Name': 'instance-id', 'Values': params['instance_ids']}]})

        instances, account_id = ec2_connector.list_instances(**instance_filter)

        _LOGGER.debug(f'[list_instances] [{params["region_name"]}] INSTANCE COUNT : {len(instances)}')

        if instances:
            ins_manager = EC2InstanceManager(params, ec2_connector=ec2_connector)
            asg_manager = AutoScalingGroupManager(params)
            elb_manager = LoadBalancerManager(params, ec2_connector=ec2_connector)
            disk_manager = DiskManager(params)
            nic_manager = NICManager(params)
            vpc_manager = VPCManager(params)
            sg_manager = SecurityGroupManager(params)
            cw_manager = CloudWatchManager()

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
                                                                 vpcs, subnets, region_name)

                    nic_vos = nic_manager.get_nic_info(instance.get('NetworkInterfaces'), subnet_vo)

                    sg_ids = [security_group.get('GroupId') for security_group in instance.get('SecurityGroups', []) if
                              security_group.get('GroupId') is not None]
                    sg_rules_vos = sg_manager.get_security_group_info(sg_ids, sgs)

                    if disk_vos:
                        server_data['data']['aws']['root_volume_type'] = disk_vos[0].get('tags', {}).get('volume_type')

                    server_data.update({
                        'region_code': region_name,
                        'instance_type': server_data['data']['compute']['instance_type'],
                        'tags': convert_tags(instance.get('Tags', []))
                    })

                    server_data['data'].update({
                        'primary_ip_address': instance_ip,
                        'nics': nic_vos,
                        'disks': disk_vos,
                        'load_balancer': load_balancer_vos,
                        'security_group': sg_rules_vos,
                        'vpc': vpc_vo,
                        'subnet': subnet_vo
                    })

                    if auto_scaling_group_vo:
                        server_data['data'].update({
                            'auto_scaling_group': auto_scaling_group_vo
                        })

                    # IP addr : ip_addresses = nics.ip_addresses + data.public_ip_address
                    server_data.update({
                        'ip_addresses': self.merge_ip_addresses(server_data)
                    })

                    server_data['data']['cloudwatch'] = cw_manager.set_cloudwatch_info(instance_id, region_name)
                    server_data['data']['cloudtrail'] = self.set_cloudtrail(region_name, cloudtrail_resource_type,
                                                                            instance_id)
                    server_data['data']['compute']['account'] = account_id
                    server_data['account'] = account_id

                    server_data.update({
                        '_metadata': meta_manager.get_server_metadata(),
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
    def set_cloudtrail(region_name, resource_type, resource_name):
        cloudtrail = {
            'LookupAttributes': [
                {
                    "AttributeKey": "ResourceName",
                    "AttributeValue": resource_name,
                }
            ],
            'region_name': region_name,
            'resource_type': resource_type
        }
        return CloudTrail(cloudtrail, strict=False)

    @staticmethod
    def list_cloud_service_types():
        meta_manager: MetadataManager = MetadataManager()

        cloud_service_type = {
            '_metadata': meta_manager.get_cloud_service_type_metadata(),
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
    def get_device_for_cloudwatch(disks):
        try:
            for _disk in disks:
                _device = _disk.device
                _device_name = _device.split('/')[-1]
                if _device_name:
                    return f'{_device_name}1'

            return None
        except Exception as e:
            return None

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
