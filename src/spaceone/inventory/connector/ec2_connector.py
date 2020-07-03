# -*- coding: utf-8 -*-

__all__ = ["EC2Connector"]

import os
import os.path
# AWS SDK for Python
import boto3
import json
import requests
import logging
import urllib.request
import pprint

from multiprocessing import Pool

from datetime import datetime
from spaceone.core.transaction import Transaction
from spaceone.inventory.error import *
from spaceone.core.error import *
from spaceone.core import utils
from spaceone.core.connector import BaseConnector

_LOGGER = logging.getLogger(__name__)

RESOURCES = ['cloudformation', 'cloudwatch', 'dynamodb', 'ec2', 'glacier', 'iam', 'opsworks', 's3', 'sns', 'sqs']
DEFAULT_REGION = 'us-east-1'
NUMBER_OF_CONCURRENT = 4
PRICE_URL = 'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.json'
EC2_TYPE_DIR = f'{os.path.abspath(__file__)}/conf'
TMP_DIR = '/tmp'
DEFAULT_FILE = 'ec2_type.json'

EC2_MAX_LIMIT = 1000

class EC2Connector(BaseConnector):

    def __init__(self, transaction, config):
        super().__init__(transaction, config)

    def verify(self, options, secret_data):
        # This is connection check for AWS
        region_name = secret_data.get('region_name', DEFAULT_REGION)
        _set_connect(secret_data, region_name)
        return "ACTIVE"

    def get_all_regions(self, secret_data, region_name):
        """ Find all region name
        Args:
            secret_data: secret data
            region_name (list): list of region_name if wanted

        Returns: list of region name
        """
        # From secret
        if 'region_name' in secret_data:
            return [secret_data['region_name']]

        # From region_name
        if len(region_name) > 0:
            return region_name

        # From all regions
        region_name = DEFAULT_REGION
        client, resource = _set_connect(secret_data, region_name)
        try:
            regions = client.describe_regions()
            region_list = []
            for region in regions['Regions']:
                region_list.append(region['RegionName'])
            return region_list
        except Exception as e:
            raise ERROR_PLUGIN_VERIFY_FAILED(plugin='aws-ec2', secret=list(secret_data))

    def collect_info(self, query, secret_data):
        """
        Args:
            query (dict): example
                  {
                      'instance_id': ['i-123', 'i-2222', ...]
                      'instance_type': 'm4.xlarge',
                      'region_name': ['aaaa']
                  }
        If there is regiona_name in query, this indicates searching only these regions
        """

        (query, instance_ids, region_name) = self._check_query(query)
        post_filter_cache = False if len(region_name) > 0 else True

        query.append({'Name': 'instance-state-name', 'Values': ['running', 'shutting-down', 'stopping', 'stopped']})

        #ec2_type_dic = self._get_ec2_type_file()
        regions = self.get_all_regions(secret_data, region_name)
        params = []
        region_name_list = []  # For filter_cache
        for region in regions:
            params.append({
                'region_name': region,
                'query': query,
                'secret_data': secret_data,
                #'ec2_type': ec2_type_dic,
                'instance_ids': instance_ids
            })

        with Pool(NUMBER_OF_CONCURRENT) as pool:

            result = pool.map(discover_ec2, params)

            for resources in result:

                #print(f'resources: {resources}')
                (collected_resources, region_name) = resources
                if len(collected_resources) > 0:
                    region_name_list.append(region_name)

                for resource in collected_resources:
                    try:
                        response = _prepare_response_schema()
                        response['resource'] = resource

                        yield response
                    except Exception as e:
                        _LOGGER.error(f'[collect_info] skip return {resource}, {e}')

        # Return FilterCache
        try:
            if post_filter_cache:
                filter_cache_response = _prepare_filter_cache_response_schema()
                filter_cache_response['resource'] = {'region_name': region_name_list}
                yield filter_cache_response
        except Exception as e:
            _LOGGER.error(f'[collect_info] skip return filter_cache resource, {e}')

    def _check_query(self, query):
        instance_ids = []
        filters = []
        region_name = []
        for key, value in query.items():
            if key == 'instance_id' and isinstance(value, list):
                instance_ids = value

            elif key == 'region_name' and isinstance(value, list):
                region_name.extend(value)

            else:
                if isinstance(value, list) == False:
                    value = [value]

                if len(value) > 0:
                    filters.append({'Name': key, 'Values': value})

        return (filters, instance_ids, region_name)


#######################
# AWS Boto3 session
#######################
def create_session(secret_data: dict, options={}):
    _check_secret_data(secret_data)

    aws_access_key_id = secret_data['aws_access_key_id']
    aws_secret_access_key = secret_data['aws_secret_access_key']
    role_arn = secret_data.get('role_arn')

    try:
        if role_arn:
            return _create_session_with_assume_role(aws_access_key_id, aws_secret_access_key, role_arn)
        else:
            return _create_session_with_access_key(aws_access_key_id, aws_secret_access_key)
    except Exception as e:
        raise ERROR_INVALID_CREDENTIALS()

def _check_secret_data(secret_data):
    if 'aws_access_key_id' not in secret_data:
        raise ERROR_REQUIRED_PARAMETER(key='secret.aws_access_key_id')

    if 'aws_secret_access_key' not in secret_data:
        raise ERROR_REQUIRED_PARAMETER(key='secret.aws_secret_access_key')

def _create_session_with_access_key(aws_access_key_id, aws_secret_access_key):
    session = boto3.Session(aws_access_key_id=aws_access_key_id,
                                 aws_secret_access_key=aws_secret_access_key)

    sts = session.client('sts')
    sts.get_caller_identity()
    return session

def _create_session_with_assume_role(aws_access_key_id, aws_secret_access_key, role_arn):
    session = _create_session_with_access_key(aws_access_key_id, aws_secret_access_key)

    sts = session.client('sts')
    assume_role_object = sts.assume_role(RoleArn=role_arn, RoleSessionName=utils.generate_id('AssumeRoleSession'))
    credentials = assume_role_object['Credentials']

    session = boto3.Session(aws_access_key_id=credentials['AccessKeyId'],
                            aws_secret_access_key=credentials['SecretAccessKey'],
                            aws_session_token=credentials['SessionToken'])
    return session


def _set_connect(secret_data, region_name, service="ec2"):
    """
    """
    session = create_session(secret_data)
    aws_conf = {}
    aws_conf['region_name'] = region_name

    if service in RESOURCES:
        resource = session.resource(service, **aws_conf)
        client = resource.meta.client
    else:
        resource = None
        client = session.client(service, region_name=region_name)
    return client, resource




def discover_ec2(params):
    """
    Args: params (dict): {
                'region_name': 'str',
                'query': 'dict',
                'secret_data': 'dict',
                #'ec2_type': 'dict',
                'instance_ids', 'list'
            }

    Returns: Resources, region_name
    """
    print(f'[discover_ec2] {params["region_name"]}')

    client, resource = _set_connect(params['secret_data'], params['region_name'])
    try:
        resources = _list_instances(client,
                                    params['query'],
                                    params['instance_ids'],
                                    #params['ec2_type'],
                                    params['region_name'],
                                    params['secret_data']
                                    )


        return resources
    except Exception as e:
        _LOGGER.error(f'[discover_ec2] skip region: {params["region_name"]}, {e}')


def _get_OS_distro(os):
    os_distros = []
    os_distros.append({'centos': ['centos']})
    os_distros.append({'ubuntu': ['ubuntu']})
    os_distros.append({'redhat': ['rhel']})
    os_distros.append({'debian': ['debian']})
    os_distros.append({'fedora': ['fedora']})
    os_distros.append({'win2012r2-std': ['windows', '2012', 'r2', 'standard']})
    os_distros.append({'win2008r2-std': ['windows', '2008', 'r2', 'standard']})
    os_distros.append({'amazonlinux': ['amazon']})
    os_distros.append({'amazonlinux': ['ami']})

    for os_distro in os_distros:
        flag = True
        for v in list(os_distro.values())[0]:
            flag = (v in os.lower())

        if flag:
            return list(os_distro.keys())[0]

    return 'unknown'


def _get_image_info(client, ids=None):
    result = {}
    query = {}
    if ids:
        query['ImageIds'] = ids

    images = client.describe_images(**query)
    for image in images['Images']:
        result[image['ImageId']] = image

    return result


def _get_volume_info(client, ids=None):
    result = {}
    query = {}
    if ids:
        query['VolumeIds'] = ids

    volumes = client.describe_volumes(**query)

    for volume in volumes['Volumes']:
        result[volume['VolumeId']] = volume

    return result


def _get_security_group_info(client, ids=None):
    result = {}
    query = {}
    if ids:
        query['GroupIds'] = ids

    security_groups = client.describe_security_groups(**query)
    for security_group in security_groups['SecurityGroups']:
        result[security_group['GroupId']] = {}
        result[security_group['GroupId']]['name'] = security_group['GroupName']
        result[security_group['GroupId']]['rules'] = _get_security_group_rules(security_group)

    return result


def _get_subnet_info(client, ids=None):
    result = {}
    query = {}
    if ids:
        query['SubnetIds'] = ids

    subnets = client.describe_subnets(**query)
    for subnet in subnets['Subnets']:
        result[subnet['SubnetId']] = subnet

    return result


def _getvpcInfo(client, ids=None):
    result = {}
    query = {}
    if ids:
        query['VpcIds'] = ids

    vpcs = client.describe_vpcs(**query)
    for vpc in vpcs['Vpcs']:
        result[vpc['VpcId']] = vpc

    return result


def _get_elasticip_info(client, ids=None):
    result = {}
    query = {}
    filters = []
    key = "instance-id"

    if ids:
        # filters.append({'Name':key,'Values':[ids]})
        query["Filters"] = filters
    eips = client.describe_addresses(**query)
    for eip in eips["Addresses"]:
        if "InstanceId" in eip.keys():
            result[eip["InstanceId"]] = eip

    return result


def _get_security_group_rules(sg_info):
    sg_rules = []

    for inbound_rule in sg_info.get('IpPermissions', []):
        rule = {}

        rule['security_group_id'] = sg_info['GroupId']
        rule['security_group_name'] = sg_info['GroupName']
        rule['direction'] = 'inbound'

        # Src CIDR | Src name
        for ip_range in inbound_rule['IpRanges']:
            rule['remote'] = ip_range['CidrIp']
            rule['remote_cidr'] = ip_range['CidrIp']
            if "Description" in ip_range.keys():
                rule["description"] = ip_range['Description']
            else:
                rule["description"] = "-"


        for remote_sg in inbound_rule['UserIdGroupPairs']:
            rule['remote'] = remote_sg['GroupId']
            rule['remote_id'] = remote_sg['GroupId']

            if "Description" in remote_sg.keys():
                rule["description"] = remote_sg['Description']
            else:
                rule["description"] = "-"

        # Protocol
        protocol = 'all' if inbound_rule['IpProtocol'] == '-1' else inbound_rule['IpProtocol']
        rule['protocol'] = protocol.upper()

        # description


        # Dst name
        rule['port_range_min'] = inbound_rule.get('FromPort', 0)
        rule['port_range_max'] = inbound_rule.get('ToPort', 65535)
        if rule['port_range_min'] == rule['port_range_max']:
            rule["port"] = str(rule['port_range_min'])
        else:
            rule["port"] = str(rule['port_range_min']) + " - " + str(rule['port_range_max'])

        sg_rules.append(rule.copy())



    for outbound_rule in sg_info.get('IpPermissionsEgress', []):
        rule = {}

        rule['security_group_id'] = sg_info['GroupId']
        rule['security_group_name'] = sg_info['GroupName']
        rule['direction'] = 'outbound'

        # Protocol
        protocol = 'all' if outbound_rule['IpProtocol'] == '-1' else outbound_rule['IpProtocol']
        rule['protocol'] = protocol.upper()

        # Dst name CIDR and Port
        rule['port_range_min'] = outbound_rule.get('FromPort', 0)
        rule['port_range_max'] = outbound_rule.get('ToPort', 65535)

        if rule['port_range_min'] == rule['port_range_max']:

            rule["port"] = str(rule['port_range_min'])
        else:
            rule["port"] = str(rule['port_range_min']) + " - " + str(rule['port_range_max'])

        for ip_range in outbound_rule['IpRanges']:
            rule['remote'] = ip_range['CidrIp']
            rule['remote_cidr'] = ip_range['CidrIp']
            if "Description" in ip_range.keys():
                rule["description"] = ip_range['Description']
            else:
                rule["description"] = "-"



        for remote_sg in outbound_rule['UserIdGroupPairs']:
            rule['remote'] = remote_sg['GroupId']
            rule['remote_id'] = remote_sg['GroupId']

            if "Description" in remote_sg.keys():
                rule["description"] = remote_sg['Description']
            else:
                rule["description"] = "-"


        sg_rules.append(rule.copy())

    return sg_rules


def _get_single_instance(client, instance_query, instance_ids):
    instance_list = []
    for instance_id in instance_ids:
        try:
            instances = client.describe_instances(InstanceIds=[instance_id], **instance_query)['Reservations']
            instance_list.append(instances[0])
        except Exception as e:
            _LOGGER.debug(f'[_get_single_instance] failed: {e}')
    return instance_list

def _get_instances(client, instance_query):
    instance_list = []
    limit = EC2_MAX_LIMIT
    page_size = 50
    paginator = client.get_paginator('describe_instances')
    page_config = {'MaxItems': limit, 'PageSize': page_size}
    response_iterator = paginator.paginate(PaginationConfig=page_config, **instance_query)
    for response in response_iterator:
        instance_list.extend(response['Reservations'])
    return instance_list

def _get_instance_type(client, instance_types):
    result = {}
    instance_type_list = client.describe_instance_types(InstanceTypes=instance_types)['InstanceTypes']
    for inst_type in instance_type_list:
        name = inst_type['InstanceType']
        item = {'name': name,
                'core': inst_type['VCpuInfo']['DefaultVCpus'],
                'memory': inst_type['MemoryInfo']['SizeInMiB'] / 1024
                }
        result[name] = item
    return result


def _list_instances(client, query, instance_ids, region_name, secret_data):
    resource_list = []
    instance_query = {}
    autoscaling_query = {}
    # target_group_query = {}
    instance_query['Filters'] = query
    instances = []
    # target_group_query["TargetGroupArn"] = 
    # "arn:aws:elasticloadbalancing:ap-northeast-2:072548720675:targetgroup/dev-tools-target-group/d9cd02f12787288e"
    try:
        if len(instance_ids) > 0:
            # search per instances, since if one of instance_id does not exist, describe will be failed
            instances = _get_single_instance(client, instance_query, instance_ids)
        else:
            instances = _get_instances(client, instance_query)

        if len(instances) == 0:
            # Fast return if No resources
            print(f'Return now, no data at {region_name}')
            return resource_list, region_name

        client_ec2, resource_ec2 = _set_connect(secret_data, region_name, "ec2")
        client_autoscaling, resource_autoscaling = _set_connect(secret_data, region_name, "autoscaling")
        client_elb, resource_elb = _set_connect(secret_data, region_name, "elb")
        client_elbv2, resource_elbv2 = _set_connect(secret_data, region_name, "elbv2")

        auto_scaling_groups = client_autoscaling.describe_auto_scaling_groups(**autoscaling_query)["AutoScalingGroups"]
        launch_configurations = client_autoscaling.describe_launch_configurations()["LaunchConfigurations"]

        elbs = client_elb.describe_load_balancers()
        elbs_v2 = client_elbv2.describe_load_balancers()
        _ec2 = client_ec2.describe_instances()

        target_groups = client_elbv2.describe_target_groups()["TargetGroups"]

    except Exception as e:
        print(f'[_list_instances] Fail to describe instances: {e}')
        return resource_list, region_name

    instance_dic = {}
    image_dic = {}
    volume_dic = {}
    subnet_dic = {}
    sg_dic = {}
    vpc_dic = {}
    eip_dic = {}
    target_group_dic = {}
    elb_dic = {}
    launch_configuration_dic = {}

    # Find Resources
    instance_types = set([])
    for instance in instances:

        owner_id = instance['OwnerId']
        instance = instance['Instances'][0]
        if (instance_ids) and (instance['InstanceId'] not in instance_ids):
            continue

        instance_dic[instance['InstanceId']] = instance
        instance_dic[instance['InstanceId']]['OwnerId'] = owner_id
        image_dic[instance['ImageId']] = None

        instance_types.add(instance['InstanceType'])    # For ec2_type

        for sg in instance['SecurityGroups']:
            sg_dic[sg['GroupId']] = None

        for nic in instance['NetworkInterfaces']:
            subnet_dic[nic['SubnetId']] = None
            vpc_dic[nic["VpcId"]] = None

        for volume in instance['BlockDeviceMappings']:

            volume_dic[volume['Ebs']['VolumeId']] = None

    ec2_type = _get_instance_type(client, list(instance_types))

    # get target group and health status
    for target_group in target_groups:
        if target_group["LoadBalancerArns"]:
            target_group_query = {}
            target_group_dic[target_group["TargetGroupArn"]] = target_group
            target_group_query["TargetGroupArn"] = target_group["TargetGroupArn"]
            target_group_health = client_elbv2.describe_target_health(**target_group_query)["TargetHealthDescriptions"]
            target_group_dic[target_group["TargetGroupArn"]]["TargetHealthDescriptions"] = target_group_health

    # for elb list
    for elb_v2 in elbs_v2["LoadBalancers"]:
        elb_dic[elb_v2["LoadBalancerArn"]] = elb_v2

    for launch_configuration in launch_configurations:
        launch_configuration_dic[launch_configuration["LaunchConfigurationName"]] = launch_configuration

    image_dic = _get_image_info(client, list(image_dic.keys()))
    volume_dic = _get_volume_info(client, list(volume_dic.keys()))
    sg_dic = _get_security_group_info(client, list(sg_dic.keys()))
    subnet_dic = _get_subnet_info(client, list(subnet_dic.keys()))
    vpc_dic = _getvpcInfo(client, list(vpc_dic.keys()))
    eip_dic = _get_elasticip_info(client, instance['InstanceId'])

    # Fill Resource Data
    for instance_id, instance in instance_dic.items():
        instance_itype = ec2_type.get(instance['InstanceType'], {'name': 'unknown', 'core': 0, 'memory': 0})
        image_info = image_dic.get(instance['ImageId'], {})

        dic = {}
        dic['name'] = ''
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                dic['name'] = tag['Value']

        az = instance['Placement']['AvailabilityZone']

        dic['server_type'] = 'VM'

        dic['ip_addresses'] = []
        dic['data'] = {}
        dic['os_type'] = instance.get('Platform', 'LINUX').upper()
        # dic['os_type'] = _guest(instance.get('Platform','LINUX'))

        ###############
        # data.hardware
        ###############
        dic['data']['hardware'] = {}
        dic['data']['hardware']['core'] = instance_itype['core']
        dic['data']['hardware']['memory'] = instance_itype['memory']

        #########################
        # data.auto_scaling_group#
        #########################

        dic["data"]["auto_scaling_group"] = {}

        for auto_scaling_group in auto_scaling_groups:
            if "Instances" in auto_scaling_group.keys():
                for asg_instances in auto_scaling_group["Instances"]:
                    if asg_instances["InstanceId"] == instance_id:
                        #print(auto_scaling_group)
                        dic["data"]["auto_scaling_group"]["name"] = auto_scaling_group["AutoScalingGroupName"]
                        dic["data"]["auto_scaling_group"]["arn"] = auto_scaling_group["AutoScalingGroupARN"]
                        if "LaunchConfigurationName" in auto_scaling_group.keys():
                            dic["data"]["auto_scaling_group"]["launch_configuration_name"] = auto_scaling_group[
                                "LaunchConfigurationName"]
                            dic["data"]["auto_scaling_group"]["launch_configuration_arn"] = \
                                launch_configuration_dic[auto_scaling_group[
                                    "LaunchConfigurationName"]]["LaunchConfigurationARN"]



        #############
        # data.os
        #############
        dic['data']['os'] = {}
        dic['data']['os']['os_arch'] = image_info.get('Architecture', '')
        dic['data']['os']['os_distro'] = _get_OS_distro(image_info.get('Name', ''))

        ################
        # data.compute
        ################
        dic['data']['compute'] = {}
        dic['data']['compute']['account_id'] = instance['OwnerId']
        dic['data']['compute']['instance_id'] = instance['InstanceId']
        dic['data']['compute']['instance_name'] = dic['name']
        dic['data']['compute']['instance_type'] = instance['InstanceType']
        dic['data']["compute"]['az'] = az
        dic['data']['compute']['image'] = image_info.get('Name', '')
        dic["data"]["compute"]["region_name"] = region_name

        if 'KeyName' in instance:
            dic['data']['compute']['keypair'] = instance['KeyName']
        dic["data"]["compute"]["instance_state"] = instance["State"]["Name"]
        dic["data"]["compute"]["launched_at"] = instance["LaunchTime"].strftime('%Y-%m-%d')

        ################
        # data.aws
        ################

        dic["data"]["aws"] = {}

        dic["data"]["aws"]["ebs_optimized"] = instance["EbsOptimized"]

        dic["data"]["aws"]["lifecycle"] = instance.get("InstanceLifecycle", 'normal')

        if "IamInstanceProfile" in instance.keys():
            dic["data"]["aws"]["iam_instance_profile"] = {}
            dic["data"]["aws"]["iam_instance_profile"]["arn"] = instance["IamInstanceProfile"]["Arn"]
            dic["data"]["aws"]["iam_instance_profile"]["id"] = instance["IamInstanceProfile"]["Id"]
            arn_name = instance["IamInstanceProfile"]["Arn"].split("/")
            dic["data"]["aws"]["iam_instance_profile"]["name"] = arn_name[-1]

        ################
        # data.vpc
        ################
        vpc_tags = []
        dic["data"]["vpc"] = {}
        dic["data"]["vpc"]["vpc_id"] = instance["VpcId"]
        dic["data"]["vpc"]["cidr"] = vpc_dic[instance["VpcId"]]["CidrBlockAssociationSet"][0]["CidrBlock"]
        # dic['data']["vpc"]['vpc_name'] = "unknown"

        if 'Tags' in vpc_dic[instance['VpcId']].keys():
            vpc_tags = vpc_dic[instance['VpcId']]["Tags"]

        for vpc_tag in vpc_tags:

            if vpc_tag['Key'] == "Name":
                dic['data']['vpc']['vpc_name'] = vpc_tag["Value"]

        if "vpc_name" not in dic['data']["vpc"].keys():
            dic['data']["vpc"]['vpc_name'] = ""

        dic["data"]["vpc"][
            "vpc_arn"] = f"arn:aws:ec2:{region_name}:{instance['OwnerId']}:vpc/{dic['data']['vpc']['vpc_id']}"

        ################
        # data.subnet
        ################
        subnet_tags = []
        dic["data"]["subnet"] = {}

        dic["data"]["subnet"]["subnet_id"] = instance['SubnetId']
        dic["data"]["subnet"]["vpc_id"] = subnet_dic[instance['SubnetId']]["VpcId"]
        dic["data"]["subnet"]["cidr"] = subnet_dic[instance['SubnetId']]["CidrBlock"]

        if 'Tags' in subnet_dic[instance['SubnetId']].keys():
            subnet_tags = subnet_dic[instance['SubnetId']]["Tags"]

        for subnet_tag in subnet_tags:

            if subnet_tag['Key'] == "Name":
                dic['data']["subnet"]['subnet_name'] = subnet_tag["Value"]

        if "subnet_name" not in dic['data']["subnet"].keys():
            dic['data']["subnet"]['subnet_name'] = ""

        dic["data"]["subnet"][
            "subnet_arn"] = f"arn:aws:ec2:{region_name}:{instance['OwnerId']}:vpc/{dic['data']['subnet']['subnet_id']}"

        #############################
        # data.security_group_rules #
        #############################
        ## dest_remote_id

        dic['data']['compute']['security_groups'] = []
        dic['data']['security_group_rules'] = []

        for security_group in instance['SecurityGroups']:
            sg_info = sg_dic[security_group['GroupId']]

            dic['data']['compute']['security_groups'].append(sg_info['name'])

            dic['data']['security_group_rules'] += sg_info['rules']

        ##################
        # data.public_ip_address #
        ##################

        if 'PublicIpAddress' in instance.keys():
            dic["data"]["public_ip_address"] = instance["PublicIpAddress"]

        ##################
        # data.PublicDnsName #
        ##################

        if 'PublicDnsName' in instance.keys():
            dic["data"]["public_dns"] = instance["PublicDnsName"]

        ################
        # data.nics
        ################

        # nics tags 삭제 별로 필요 없음
        dic['nics'] = []

        for nic in instance['NetworkInterfaces']:
            nic_dic = {}
            nic_dic['device_index'] = nic['Attachment']['DeviceIndex']
            nic_dic['mac_address'] = nic['MacAddress']

            # 'PrivateIpAddresses': [{'Primary': True, 'PrivateDnsName': 'ip-172-16-18-84.ap-northeast-2.compute.internal', 'PrivateIpAddress': '172.16.18.84'}
            subnet = subnet_dic[nic['SubnetId']]
            nic_dic['cidr'] = subnet['CidrBlock']
            nic_dic['ip_addresses'] = []


            ip_list = []

            for ip_item in nic['PrivateIpAddresses']:
                ip_list.append(ip_item['PrivateIpAddress'])

            nic_dic["tags"] = {}

            if "Association" in nic.keys():
                nic_dic["public_ip_address"] = nic["Association"]["PublicIp"]
                nic_dic['tags']["public_dns"] = nic["Association"]["PublicDnsName"]

                if instance_id in eip_dic.keys() and nic["NetworkInterfaceId"] == eip_dic[instance_id]["NetworkInterfaceId"]:
                    nic_dic['tags']["eip"] = eip_dic[instance_id]["PublicIp"]

            nic_dic['ip_addresses'] = ip_list
            dic['nics'].append(nic_dic)


        dic['nics'] = sorted(dic['nics'], key=lambda k: k['device_index'])

        ###############
        # data.disk
        ###############

        dic['disks'] = []
        device_index = 0
        for volume in instance['BlockDeviceMappings']:
            disk_dic = {}

            disk_type = list(volume.keys())[-1]
            disk_dic['disk_type'] = disk_type.upper()

            disk_dic['device'] = volume['DeviceName'].split('/')[-1]
            volume = volume_dic[volume['Ebs']['VolumeId']]
            disk_dic['device_index'] = device_index
            disk_dic['size'] = float(volume['Size'])

            disk_dic["tags"] = {}
            disk_dic["tags"]["iops"] = volume["Iops"]
            disk_dic["tags"]["encrypted"] = volume["Encrypted"]
            disk_dic["tags"]['volume_id'] = volume['VolumeId']
            disk_dic["tags"]['volume_type'] = volume['VolumeType']
            print(volume['VolumeType'])
            dic['disks'].append(disk_dic)
            device_index += 1

        #########################
        #     data.elb          #
        #########################
        dic["data"]["load_balancers"] = []

        elb_list = []
        target_port_dic = {}

        for tg in target_group_dic:

            if target_group_dic[tg]["TargetType"] == "instance":
                for target in target_group_dic[tg]["TargetHealthDescriptions"]:

                    if target["Target"]["Id"] == instance_id:
                        elb_list.append(target_group_dic[tg]["LoadBalancerArns"][0])

                        #print(target_group_dic[tg]["LoadBalancerArns"][0],target["Target"]["Port"])
                        if target_group_dic[tg]["LoadBalancerArns"][0] in target_port_dic.keys():
                            target_port_dic[target_group_dic[tg]["LoadBalancerArns"][0]].append(target["Target"]["Port"])
                        else:
                            target_port_dic[target_group_dic[tg]["LoadBalancerArns"][0]] = []
                            target_port_dic[target_group_dic[tg]["LoadBalancerArns"][0]].append(
                                target["Target"]["Port"])

            if target_group_dic[tg]["TargetType"] == "ip":

                target_ip_list = []
                for target in target_group_dic[tg]["TargetHealthDescriptions"]:
                    target_ip_list.append(target["Target"]["Id"])

                nic_ip_list = []
                for ni in dic['nics']:
                    nic_ip_list.extend(ni["tags"]["ip_list"])

                overlaped_ip = list(set(target_ip_list).intersection(nic_ip_list))
                if len(overlaped_ip) > 0:
                    #print(target_group_dic[tg]["LoadBalancerArns"][0], target["Target"]["Port"])

                    elb_list.append(target_group_dic[tg]["LoadBalancerArns"][0])

                    if target_group_dic[tg]["LoadBalancerArns"][0] in target_port_dic.keys():
                        target_port_dic[target_group_dic[tg]["LoadBalancerArns"][0]].append(target["Target"]["Port"])
                    else:
                        target_port_dic[target_group_dic[tg]["LoadBalancerArns"][0]] = []
                        target_port_dic[target_group_dic[tg]["LoadBalancerArns"][0]].append(
                            target["Target"]["Port"])

        elb_list = list(set(elb_list))
        #print(target_port_dic)
        #print(instance_id, elb_list)

        for elb_lis in elb_list:
            instance_elb_dic = {}
            instance_elb_dic["name"] = elb_dic[elb_lis]["LoadBalancerName"]
            instance_elb_dic["type"] = elb_dic[elb_lis]["Type"]
            instance_elb_dic["dns"] = elb_dic[elb_lis]["DNSName"]
            instance_elb_dic["port"] = target_port_dic[elb_lis]
            instance_elb_dic["tags"] = {}
            instance_elb_dic["tags"]["scheme"] = elb_dic[elb_lis]["Scheme"]
            instance_elb_dic["tags"]["arn"] = elb_dic[elb_lis]["LoadBalancerArn"]

            dic["data"]["load_balancers"].append(instance_elb_dic)

        #########################
        #     data.tags          #
        #########################
        dic["data"]["instance_tags"] = instance["Tags"]



        ################################
        # metadata for frontend
        ################################
        metadata = _create_metadata()
        dic['metadata'] = metadata
        dic["reference"] = {}
        dic["reference"] = _create_reference_schema(region_name,
                                                    dic["data"]["compute"]["instance_id"],
                                                    dic["data"]["compute"]["account_id"])


        ################################
        # cloudwatch for monitoring
        ################################
        dic['data']['cloudwatch'] = {
            'namespace': 'AWS/EC2',
            'region_name': region_name,
            'dimensions': [
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                }
            ]
        }

        resource_list.append(dic)

    return resource_list, region_name





def _create_metadata():
    """ Create metadata for frontend view
    """

    table_layout = _create_table_layout()
    sub_data_layout = _create_sub_data()

    metadata = {
        "view": {

            'table': {

                "layout": table_layout

            },

            'sub_data': {

                'layouts': sub_data_layout

            }
        }

    }
    return metadata




#todo
def _create_table_layout():


    """ Create table


    """



    table = {}
    return table

def _badge(color):
    return {'options': {'background_color': color},
            'type': 'badge'}

def _badge_ol(color):
    return {
            "options": {
                "outline_color": color
            },
            "type": "badge"
            }

def _state(color):
    return {"options": {
                "icon": {
                    "color": color
                    },
                },
            "type": 'state',
            }


def _create_sub_data():
    """ Create Sub Data page
    """

    ec2_instance = {
        'name': 'EC2 Instance',
        'type': 'item',
        'options': {
            'fields': [{'name': 'Instance ID',      'key': 'data.compute.instance_id'},
                       {'name': 'Instance State',   'key': 'data.compute.instance_state',
                             'type': 'enum',
                             'options':
                                 {
                                     "pending": _state('yellow.500'),
                                     "running": _state('green.500'),
                                     "shutting-down": _state('gray.500'),
                                     "stopped": _state('red.500'),
                                 },
                             },
                        {'name': 'Instance Type',   'key': 'data.compute.instance_type'},
                        {'name': 'EC2 Lifecycle',   'key': 'data.aws.lifecycle',
                            'type': "enum",
                            'options':
                                 {
                                     "spot": _badge('indigo.500'),
                                     "scheduled": _badge('coral.600'),
                                     "normal": _badge('primary')
                                 }
                            },
                        {'name': 'Key Pair',        'key': 'data.compute.keypair'},
                        {'name': 'IAM Role',        'key': 'data.aws.iam_instance_profile.name'},
                        {'name': 'EBS-Optimized',   'key': 'data.aws.ebs_optimized',
                             'type': "enum",
                             'options':
                                 {
                                     'true': _badge('indigo.500'),
                                     'false': _badge('coral.600')
                                 },
                             },
                        {'name': 'AMI ID',           'key': 'data.compute.image'},
                        {'name': 'Region',          'key': 'data.compute.region_name'},
                        {'name': 'Availability Zone', 'key': 'data.compute.az'},
                        {'name': 'Public DNS', 'key': 'data.public_dns'},
                        {'name': 'Public IP', 'key': 'data.public_ip_address'},
                        # {'name': 'Elastic IPs', 'key': 'data.eip',
                        #    "type": "list",
                        #    "options": {
                        #         "item": {
                        #             "type": "badge",
                        #             "options": {
                        #                 "outline_color": "violet.500"
                        #             }
                        #         },
                        #         "delimiter": "  "
                        #     }
                        #  },
                        {'name': 'Security Groups', 'key': 'data.compute.security_groups',
                            "type": "list",
                            "options": {
                                "item": {
                                    "type": "badge",
                                    "options": {
                                        "outline_color": "violet.500"
                                    }
                                },
                                "delimiter": "<br>"
                            }
                        },
                        {'name': 'Account ID',      'key': 'data.compute.account_id'},
                        {'name': 'Launched Time ', 'key': 'data.compute.launched_at'}
                        ]
                }
            }

    auto_scaling_group = {
        'name': 'Auto Scaling Group',
        'type': 'item',
        'options': {
            'fields': [{'name': 'Auto Scaling Group', 'key': 'data.auto_scaling_group.name'},
                       {'name': 'Launch Template', 'key': 'data.auto_scaling_group.launch_configuration_name'}
                       ]
            }
    }

    vpc_and_subnet = {
        'name': 'VPC',
        'type': 'item',
        'options': {
            'fields': [{'name': 'VPC ID',          'key': 'data.vpc.vpc_id'},
                        {'name': 'VPC Name',        'key': 'data.vpc.vpc_name'},
                        {'name': 'Subnet ID',       'key': 'data.subnet.subnet_id'},
                        {'name': 'Subnet Name',     'key': 'data.subnet.subnet_name'},
                       ]
        }
    }

    aws_ec2 = {
        'name': 'AWS EC2',
        'type': 'list',
        'options': {'layouts': [ ec2_instance, vpc_and_subnet, auto_scaling_group ] }
    }

    disk = {
        'name': 'Disk',
        'type': 'table',
        'options': {
            'root_path': 'disks',
            'fields': [
                        {'name': 'Index', 'key': 'device_index'},
                        {'name': 'Name', 'key': 'device'},
                        {'name': 'Volume ID', 'key': 'tags.volume_id'},
                        {'name': 'Volume Type', 'key': 'tags.volume_type',
                         'type': "enum",
                         'options':
                             {
                                 'gp2': _badge_ol('primary'),
                                 'io1': _badge_ol('indigo.500'),
                                 'sc1': _badge_ol('coral.600'),
                                 'st1': _badge_ol('peacock.500'),
                                 'standard': _badge_ol('green.500')
                             }
                         },
                        {'name': 'IOPS', 'key': 'tags.iops'},
                        {'name': 'Size(GiB)', 'key': 'size'},
                        {'name': 'Encrypted', 'key': 'tags.encrypted',
                             'type': "enum",
                             'options':
                                 {
                                     'true': _badge('indigo.500'),
                                     'false': _badge('coral.600')
                                 }
                        }

                ]
            }
    }

    nic = {
        'name': 'NIC',
        'type': 'table',
        'options': {
            'root_path': 'nics',
            'fields': [
                {'name': 'Index', 'key': 'device_index'},
                {'name': 'MAC Address', 'key': 'mac_address'},
                {'name': 'IP Addresses', 'key': 'ip_addresses',
                     'type': 'list',
                     'options': {
                         'item': {
                             'type': 'text',
                            },
                        },
                    },
                {'name': 'Elastic IP', 'key': 'tags.eip'},
                {'name': 'Public DNS', 'key': 'tags.public_dns'},
            ]
        }
    }

    sg_rules = {
        'name': 'Security Group',
        'type': 'table',
        'options': {
            'root_path': 'data.security_group_rules',
            'fields': [
                {'name': 'Direction', 'key': 'direction',
                     'type': "enum",
                     'options':
                         {
                             "inbound": _badge('indigo.500'),
                             "outbound": _badge('coral.600'),
                         },
                 },
                {'name': 'Name', 'key': 'security_group_name'},
                {'name': 'Remote', 'key': 'remote'},
                {'name': 'Port', 'key': 'port'},
                {'name': 'Protocol', 'key': 'protocol'},
                {'name': 'Description', 'key': 'description'}
            ]
        }
    }

    load_balancers = {
        'name': 'ELB',
        'type': 'table',
        'options': {
            'root_path': 'data.load_balancers',
            'fields': [
                {'name': 'Name', 'key': 'name'},
                {'name': 'DNS', 'key': 'dns'},
                {'name': 'Type', 'key': 'type',
                 'type': "enum",
                 'options':
                     {
                         "network": _badge('indigo.500'),
                         "application": _badge('coral.600')
                     },
                 },
                {'name': 'Port', 'key': 'port',
                 'type': 'list',
                 'options': {
                  'item': {
                             'type': 'text',
                            },
                        }
                },
                {'name': 'Scheme', 'key': 'tags.scheme',
                    'type': 'enum',
                    'options':
                        {
                            'internet-facing': _badge('indigo.500'),
                            'internal': _badge('coral.500')
                        },
                 },
            ]
        }
    }

    instance_tags = {
        'name': 'Tags',
        'type': 'table',
        'options': {
            'root_path': 'data.instance_tags',
            'fields': [
                {'name': 'Key', 'key': 'Key'},
                {'name': 'Value', 'key': 'Value'}
            ]
        }
    }

    sub_data = [aws_ec2, disk, nic, sg_rules, load_balancers, instance_tags]
    return sub_data


def _create_reference_schema(region, instance_id, account_id):
    arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
    link = f"https://{region}.console.aws.amazon.com/ec2/v2/home?region={region}#Instances:instanceId={instance_id}"
    return {

        "resource_id": arn,
        "external_link": link

    }


def _prepare_response_schema() -> dict:
    return {
        'state': 'SUCCESS',
        'resource_type': 'inventory.Server',
        'match_rules': {
            '1': ['data.compute.instance_id']
        },
        'replace_rules': {},
        "reference": {},
        'resource': {
        }
    }


def _prepare_filter_cache_response_schema() -> dict:
    return {
        'state': 'SUCCESS',
        'resource_type': 'inventory.FilterCache',
        'match_rules': {
        },
        'replace_rules': {},
        'resource': {
        }
    }


if __name__ == "__main__":
    import os

    # aki = os.environ.get('AWS_ACCESS_KEY_ID', "<YOUR_AWS_ACCESS_KEY_ID>")
    # sak = os.environ.get('AWS_SECRET_ACCESS_KEY', "<YOUR_AWS_SECRET_ACCESS_KEY>")
    aki = os.environ.get('AWS_ACCESS_KEY_ID', None)
    sak = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
    role_arn = os.environ.get('ROLE_ARN', None)
    if role_arn:
        secret_data = {
            #        'region_name': 'ap-northeast-2',
            'aws_access_key_id': aki,
            'aws_secret_access_key': sak,
            'role_arn': role_arn
        }
    else:
        secret_data = {
            #        'region_name': 'ap-northeast-2',
            'aws_access_key_id': aki,
            'aws_secret_access_key': sak
        }
    conn = EC2Connector(Transaction(), secret_data)
    opts = conn.verify({}, secret_data)

    print(opts)
    #query = {'region_name': ['ap-northeast-1']}
    #query = {'instance_id': ['i-0745c928020bed89f'], 'region_name': ['ap-northeast-2']}
    #query = {'instance_id': ['i-0873656da2e3af584', 'i-123'], 'region_name': ['ap-northeast-1', 'ap-northeast-2']}
    # query = {'instance_id': ['i-0873656da2e3af584'], 'region_name': ['ap-northeast-2']}
    query = {}
    from datetime import datetime

    a = datetime.now()
    resource_stream = conn.collect_info(query=query, secret_data=secret_data)
    b = datetime.now()
    c = b - a
    print(f'Computing time: {c}')
    import pprint
    for resource in resource_stream:
        pprint.pprint(resource)


