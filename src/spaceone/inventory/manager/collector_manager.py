__all__ = ['CollectorManager']

import time
import logging
from spaceone.core.manager import BaseManager
from spaceone.inventory.connector import EC2Connector
from spaceone.inventory.manager.ec2 import EC2InstanceManager, AutoScalingGroupManager, LoadBalancerManager, \
    DiskManager, NICManager, VPCManager, SecurityGroupRuleManager
from spaceone.inventory.manager.metadata.metadata_manager import MetadataManager
from spaceone.inventory.model.server import Server, ReferenceModel

_LOGGER = logging.getLogger(__name__)


class CollectorManager(BaseManager):

    def __init__(self, transaction):
        super().__init__(transaction)

    ###################
    # Verify
    ###################
    def verify(self, options, secret_data):

        """ Check connection
        """

        connector = self.locator.get_connector('EC2Connector')
        r = connector.verify(options, secret_data)
        # ACTIVE/UNKNOWN
        return r

    def list_regions(self, secret_data, region_name):
        ec2_connector: EC2Connector = self.locator.get_connector('EC2Connector')
        ec2_connector.set_client(secret_data, region_name)

        return ec2_connector.list_regions()

    def list_resources(self, params):
        print(f"=============== COLLECT :  {params['region_name']} ===============")
        start_time = time.time()
        resources = []
        ec2_connector: EC2Connector = self.locator.get_connector('EC2Connector')
        ec2_connector.set_client(params['secret_data'], params['region_name'])

        # 1. Instance list
        instances, account_id = ec2_connector.list_instances()

        print(f'INSTANCE COUNT : {len(instances)}')

        if len(instances) > 0:
            # Instance Type
            itypes = ec2_connector.list_instance_types()

            # Image
            images = ec2_connector.list_images(ImageIds=self.get_image_ids(instances))

            # Autoscaling group list
            auto_scaling_groups = ec2_connector.list_auto_scaling_groups()
            launch_configurations = ec2_connector.list_launch_configurations()

            # LB list
            load_balancers = ec2_connector.list_load_balancers()
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

            ins_manager: EC2InstanceManager = EC2InstanceManager(params, ec2_connector=ec2_connector)
            asg_manager: AutoScalingGroupManager = AutoScalingGroupManager(params)
            elb_manager: LoadBalancerManager = LoadBalancerManager(params, ec2_connector)
            disk_manager: DiskManager = DiskManager(params)
            nic_manager: NICManager = NICManager(params, ec2_connector)
            vpc_manager: VPCManager = VPCManager(params)
            sg_manager: SecurityGroupRuleManager = SecurityGroupRuleManager(params)
            meta_manager: MetadataManager = MetadataManager()

            for instance in instances:
                instance_id = instance.get('InstanceId')
                instance_ip = instance.get('PrivateIpAddress')

                server_data = ins_manager.get_server_info(instance, itypes, images, eips)
                auto_scaling_group_vo = asg_manager.get_auto_scaling_info(instance_id, auto_scaling_groups,
                                                                          launch_configurations)

                load_balancer_vos = elb_manager.get_load_balancer_info(load_balancers, target_groups,
                                                                       instance_id, instance_ip)

                disk_vos = disk_manager.get_disk_info(self.get_volume_ids(instance), volumes)
                vpc_vo, subnet_vo = vpc_manager.get_vpc_info(instance.get('VpcId'), instance.get('SubnetId'),
                                                             vpcs, subnets, params['region_name'])

                nic_vos = nic_manager.get_nic_info(instance.get('NetworkInterfaces'), subnet_vo)

                sg_ids = [security_group.get('GroupId') for security_group in instance.get('SecurityGroups', []) if security_group.get('GroupId') is not None]
                sg_rules_vos = sg_manager.get_security_group_rules_info(sg_ids, sgs)

                server_data.update({
                    'nics': nic_vos,
                    'disks': disk_vos,
                })

                server_data['data'].update({
                    'load_balancers': load_balancer_vos,
                    'security_group_rules': sg_rules_vos,
                    'auto_scaling_group': auto_scaling_group_vo,
                    'vpc': vpc_vo,
                    'subnet': subnet_vo,
                })

                # IP addr : ip_addresses = data.compute.eip + nics.ip_addresses + data.public_ip_address
                server_data.update({
                    'ip_addresses': self.merge_ip_addresses(server_data)
                })

                server_data['data']['compute']['account_id'] = account_id

                server_data.update({
                    '_metadata': meta_manager.get_metadata(),
                })

                resources.append(Server(server_data, strict=False))

        print(f'   [{params["region_name"]}] Finished {time.time() - start_time} Seconds')
        return resources

    def get_volume_ids(self, instance):
        block_device_mappings = instance.get('BlockDeviceMappings', [])
        return [block_device_mapping['Ebs']['VolumeId'] for block_device_mapping in block_device_mappings if block_device_mapping.get('Ebs') is not None]

    def get_image_ids(self, instances):
        return [instance.get('ImageId') for instance in instances if instance.get('ImageId') is not None]

    def merge_ip_addresses(self, server_data):
        compute_data = server_data['data']['compute']
        nics = server_data['nics']

        nic_ip_addresses = []
        for nic in nics:
            nic_ip_addresses.extend(nic.ip_addresses)

        merge_ip_address = compute_data.eip + nic_ip_addresses

        if server_data['data']['public_ip_address'] != '':
            merge_ip_address.append(server_data['data']['public_ip_address'])

        return list(set(merge_ip_address))

