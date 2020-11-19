__all__ = ['CollectorManager']

import time
import logging
from spaceone.core.manager import BaseManager
from spaceone.inventory.connector import EC2Connector
from spaceone.inventory.manager.ec2 import EC2InstanceManager, AutoScalingGroupManager, LoadBalancerManager, \
    DiskManager, NICManager, VPCManager, SecurityGroupManager, CloudWatchManager
from spaceone.inventory.manager.metadata.metadata_manager import MetadataManager
from spaceone.inventory.model.server import Server, ReferenceModel
from spaceone.inventory.model.region import Region
from spaceone.inventory.model.cloud_service_type import CloudServiceType


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
        server_vos = []
        ec2_connector: EC2Connector = self.locator.get_connector('EC2Connector')
        ec2_connector.set_client(params['secret_data'], params['region_name'])

        instance_filter = {}
        # Instance list and account ID
        if 'instance_ids' in params and len(params['instance_ids']) > 0:
            instance_filter.update({'Filters': [{'Name': 'instance-id', 'Values': params['instance_ids']}]})

        instances, account_id = ec2_connector.list_instances(**instance_filter)

        print(f'===== [{params["region_name"]}]  /  INSTANCE COUNT : {len(instances)}')

        if len(instances) > 0:
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
                    'nics': nic_vos,
                    'disks': disk_vos,
                    'region_code': params.get("region_name", ''),
                })

                server_data['data'].update({
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
                    'primary_ip_address': instance_ip
                })

                server_data['data']['compute']['account'] = account_id

                server_data.update({
                    '_metadata': meta_manager.get_metadata(),
                    'reference': ReferenceModel({
                        'resource_id': server_data['data']['compute']['instance_id'],
                        'external_link': f"https://{params.get('region_name')}.console.aws.amazon.com/ec2/v2/home?region={params.get('region_name')}#Instances:instanceId={server_data['data']['compute']['instance_id']}"
                    })
                })

                server_vos.append(Server(server_data, strict=False))

        return server_vos

    def list_resources(self, params):
        start_time = time.time()

        try:
            resources = self.list_instances(params)
            print(f'   [{params["region_name"]}] Finished {time.time() - start_time} Seconds')
            return resources

        except Exception as e:
            print(f'[ERROR: {params["region_name"]}] : {e}')
            raise e

    @staticmethod
    def list_cloud_service_types():
        cloud_service_type = {
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
        nics = server_data['nics']

        nic_ip_addresses = []
        for nic in nics:
            nic_ip_addresses.extend(nic.ip_addresses)

        merge_ip_address = nic_ip_addresses

        return list(set(merge_ip_address))

    @staticmethod
    def get_region_from_result(result):
        REGION_INFO = {
            'us-east-1': {'name': 'US East (N. Virginia)', 'tags': {'latitude': '39.028760', 'longitude': '-77.458263'}},
            'us-east-2': {'name': 'US East (Ohio)', 'tags': {'latitude': '40.103564', 'longitude': '-83.200092'}},
            'us-west-1': {'name': 'US West (N. California)', 'tags': {'latitude': '37.242183', 'longitude': '-121.783380'}},
            'us-west-2': {'name': 'US West (Oregon)', 'tags': {'latitude': '45.841046', 'longitude': '-119.658093'}},
            'af-south-1': {'name': 'Africa (Cape Town)', 'tags': {'latitude': '-33.932268', 'longitude': '18.424434'}},
            'ap-east-1': {'name': 'Asia Pacific (Hong Kong)', 'tags': {'latitude': '22.365560', 'longitude': '114.119420'}},
            'ap-south-1': {'name': 'Asia Pacific (Mumbai)', 'tags': {'latitude': '19.147428', 'longitude': '73.013805'}},
            'ap-northeast-3': {'name': 'Asia Pacific (Osaka-Local)', 'tags': {'latitude': '34.675638', 'longitude': '135.495706'}},
            'ap-northeast-2': {'name': 'Asia Pacific (Seoul)', 'tags': {'latitude': '37.528547', 'longitude': '126.871867'}},
            'ap-southeast-1': {'name': 'Asia Pacific (Singapore)', 'tags': {'latitude': '1.321259', 'longitude': '103.695942'}},
            'ap-southeast-2	': {'name': 'Asia Pacific (Sydney)', 'tags': {'latitude': '-33.921423', 'longitude': '151.188076'}},
            'ap-northeast-1': {'name': 'Asia Pacific (Tokyo)', 'tags': {'latitude': '35.648411', 'longitude': '139.792566'}},
            'ca-central-1': {'name': 'Canada (Central)', 'tags': {'latitude': '43.650803', 'longitude': '-79.361824'}},
            'cn-north-1': {'name': 'China (Beijing)', 'tags': {'latitude': '39.919635', 'longitude': '116.307237'}},
            'cn-northwest-1': {'name': 'China (Ningxia)', 'tags': {'latitude': '37.354511', 'longitude': '106.106147'}},
            'eu-central-1': {'name': 'Europe (Frankfurt)', 'tags': {'latitude': '50.098645', 'longitude': '8.632262'}},
            'eu-west-1': {'name': 'Europe (Ireland)', 'tags': {'latitude': '53.330893', 'longitude': '-6.362217'}},
            'eu-west-2': {'name': 'Europe (London)', 'tags': {'latitude': '51.519749', 'longitude': '-0.087804'}},
            'eu-south-1': {'name': 'Europe (Milan)', 'tags': {'latitude': '45.448648', 'longitude': '9.147316'}},
            'eu-west-3': {'name': 'Europe (Paris)', 'tags': {'latitude': '48.905302', 'longitude': '2.369778'}},
            'eu-north-1': {'name': 'Europe (Stockholm)', 'tags': {'latitude': '59.263542', 'longitude': '18.104861'}},
            'me-south-1': {'name': 'Middle East (Bahrain)', 'tags': {'latitude': '26.240945', 'longitude': '50.586321'}},
            'sa-east-1': {'name': 'South America (São Paulo)', 'tags': {'latitude': '-23.493549', 'longitude': '-46.809319'}},
            'us-gov-east-1': {'name': 'AWS GovCloud (US-East)'},
            'us-gov-west-1': {'name': 'AWS GovCloud (US)'},
        }

        match_region_info = REGION_INFO.get(getattr(result.data.compute, 'region_name', None))

        if match_region_info is not None:
            region_info = match_region_info.copy()
            region_info.update({
                'region_code': result.data.compute.region_name
            })

            return Region(region_info, strict=False)

        return None
