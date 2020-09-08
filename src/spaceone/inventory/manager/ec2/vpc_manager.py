from spaceone.core.manager import BaseManager
from spaceone.inventory.model.vpc import VPC
from spaceone.inventory.model.subnet import Subnet


class VPCManager(BaseManager):

    def __init__(self, params, ec2_connector=None):
        self.params = params
        self.ec2_connector = ec2_connector

    def get_vpc_info(self, vpc_id, subnet_id, vpcs, subnets, region_name):
        '''
        vpc_data = {
            "vpc_arn": "",
            "vpc_id": "",
            "cidr": "",
            "vpc_name": ""
        }

        subnet_data = {
            "subnet_name": "",
            "subnet_arn": "",
            "subnet_id": "",
            "cidr": ""
        }
        '''

        vpc_data = {}
        subnet_data = {}
        match_vpc = self.get_vpc(vpc_id, vpcs)
        match_subnet = self.get_subnet(subnet_id, subnets)

        if match_vpc is not None:
            vpc_data.update({
                'vpc_arn': self.generate_arn('vpc', match_vpc.get('OwnerId'), match_vpc.get('VpcId'), region_name),
                'vpc_id': match_vpc.get('VpcId'),
                'cidr': match_vpc.get('CidrBlock'),
                'vpc_name': self.generate_name(match_vpc),
            })

        if match_subnet is not None:
            subnet_data.update({
                'subnet_name': self.generate_name(match_subnet),
                'subnet_arn': match_subnet.get('SubnetArn'),
                'subnet_id': match_subnet.get('SubnetId'),
                'cidr':  match_subnet.get('CidrBlock'),
            })

        return VPC(vpc_data, strict=False), Subnet(subnet_data, strict=False)

    @staticmethod
    def get_vpc(vpc_id, vpcs):
        for vpc in vpcs:
            if vpc_id == vpc['VpcId']:
                return vpc

        return None

    @staticmethod
    def get_subnet(subnet_id, subnets):
        for subnet in subnets:
            if subnet_id == subnet['SubnetId']:
                return subnet

        return None

    @staticmethod
    def generate_arn(resource_type, owner_id, resource_id, region_name):
        return f'arn:aws:ec2:{region_name}:{owner_id}:{resource_type}/{resource_id}'

    @staticmethod
    def generate_name(resource):
        for resource_tag in resource.get('Tags', []):
            if resource_tag['Key'] == "Name":
                return resource_tag["Value"]

        return ''
