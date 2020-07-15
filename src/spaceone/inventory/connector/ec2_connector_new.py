# -*- coding: utf-8 -*-

__all__ = ["EC2Connector"]

import os
import os.path
import boto3
import json
import requests
import logging
import datetime
import traceback
from multiprocessing import Pool
from spaceone.core.transaction import Transaction
from spaceone.core.error import *
from spaceone.core import utils
from spaceone.core.connector import BaseConnector
_LOGGER = logging.getLogger(__name__)

RESOURCES = ['cloudformation', 'cloudwatch', 'dynamodb', 'ec2', 'glacier', 'iam', 'opsworks', 's3', 'sns', 'sqs']
SERVICE_NAME = 'ec2'
DEFAULT_REGION = 'us-east-1'
NUMBER_OF_CONCURRENT = 4
PRICE_URL = 'https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.json'
EC2_TYPE_DIR = f'{os.path.abspath(__file__)}/conf'
TMP_DIR = '/tmp'
DEFAULT_FILE = 'ec2_type.json'

EC2_MAX_LIMIT = 1000

class EC2Connector(BaseConnector):

    def __init__(self, transaction=None, conf=None, secret_data={}, region_name=DEFAULT_REGION, service=SERVICE_NAME):
        self.secret_data = secret_data
        self.region_name = region_name
        self.session = None
        self.ec2_client = None
        self.asg_client = None
        self.elbv2_client = None

    def get_session(self):
        _secret_data = self.secret_data
        if 'role_arn' in self.secret_data:
            return self._create_session_with_assume_role(**_secret_data)
        else:
            return self._create_session_with_access_key(**_secret_data)

    def set_client(self):
        self.session = self.get_session()
        self.ec2_client = self.session.client('ec2')
        self.asg_client = self.session.client('autoscaling')
        self.elbv2_client = self.session.client('elbv2')

    def list_regions(self):
        response = self.ec2_client.desribe_regions()
        return response['Regions']
    #new added update
    def list_instances(self):
        ec2_instances = []
        paginator = self.ec2_client.get_paginator('describe_instances')

        for reservation in paginator.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                ec2_instances.append(instance)

        return ec2_instances

    def list_auto_scaling_groups(self):
        auto_scaling_groups = []
        paginator = self.asg_client.get_paginator('describe_auto_scaling_groups')

        for asg in paginator.get('AutoScalingGroups', []):
            auto_scaling_groups.append(asg)

        return auto_scaling_groups

    def list_launch_configurations(self):
        launch_configurations = []
        paginator = self.asg_client.get_paginator('describe_launch_configurations')

        # ? launch_configurations = paginator.get('LaunchConfigurations', [])
        for auto_scaling_group in paginator.get('LaunchConfigurations', []):
            launch_configurations.append(auto_scaling_group)

        return launch_configurations

    def list_launch_templates(self):
        launch_templates = []
        paginator = self.asg_client.get_paginator('describe_launch_templates')
        for l_template in paginator.get('LaunchTemplates', []):
            launch_templates.append(l_template)

        return launch_templates

    def list_load_balancers(self):
        load_balancers =[]
        paginator = self.elbv2_client.get_paginator('describe_load_balancers')
        for load_balancer in paginator.get('LoadBalancers', []):
            load_balancers.append(load_balancer)
        return load_balancers

    def list_target_groups(self):
        paginator = self.elbv2_client.get_paginator('describe_target_groups')
        target_groups = paginator.get('TargetGroups', [])
        return target_groups

    def list_lb_listners(self):
        paginator = self.elbv2_client.get_paginator('describe_listeners')
        lb_listners = paginator.get('Listeners', [])
        return lb_listners

    def list_security_group_info(self):
        result = {}
        query = {}
        security_groups = self.ec2_client.describe_security_groups(**query)
        for security_group in security_groups['SecurityGroups']:
            result[security_group['GroupId']] = {}
            result[security_group['GroupId']]['name'] = security_group['GroupName']

        return result

    def get_subnet_info(self, ids=None):
        result = {}
        query = {}
        if ids:
            query['SubnetIds'] = ids
        subnets = self.ec2_client.describe_subnets(**query)
        for subnet in subnets.get('Subnets',[]):
            subnet_id = subnet.get('SubnetId')
            result[subnet_id] = subnet

        return result


    def get_vpc_info(self, ids=None):

        result = {}
        query = {}
        if ids:
            query['VpcIds'] = ids

        vpcs = self.ec2_client.describe_vpcs(**query)
        for vpc in vpcs.get('Vpcs',[]):
            vpc_id = vpc['VpcId']
            result[vpc_id] = vpc

        return result

    def get_volume_info(self, ids=None):
        result = {}
        query = {}
        if ids:
            query['VolumeIds'] = ids

        volumes = self.ec2_client.describe_volumes(**query)
        for volume in volumes['Volumes']:
            result[volume['VolumeId']] = volume
        return result

    def get_image_info(self, ids=None):
        result = {}
        query = {}
        if ids:
            query['ImageIds'] = ids

        images = self.ec2_client.describe_images(**query)
        for image in images['Images']:
            result[image['ImageId']] = image

        return result


    def get_elasticip_info(self, ids=None):
        result = {}
        query = {}
        filters = []

        if ids:
            # filters.append({'Name':key,'Values':[ids]})
            query["Filters"] = filters
        eips = self.ec2_client.describe_addresses(**query)
        for eip in eips["Addresses"]:
            if "InstanceId" in eip.keys():
                result[eip["InstanceId"]] = eip

        return result

    def _check_secret_data(self, secret_data):
        if 'aws_access_key_id' not in secret_data:
            raise ERROR_REQUIRED_PARAMETER(key='secret.aws_access_key_id')

        if 'aws_secret_access_key' not in secret_data:
            raise ERROR_REQUIRED_PARAMETER(key='secret.aws_secret_access_key')

    def _create_session_with_access_key(self, aws_access_key_id, aws_secret_access_key):
        session = boto3.Session(aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key)

        sts = session.client('sts')
        sts.get_caller_identity()
        return session

    def _create_session_with_assume_role(self, aws_access_key_id, aws_secret_access_key, role_arn):
        session = self._create_session_with_access_key(aws_access_key_id, aws_secret_access_key)

        sts = session.client('sts')
        assume_role_object = sts.assume_role(RoleArn=role_arn, RoleSessionName=utils.generate_id('AssumeRoleSession'))
        credentials = assume_role_object['Credentials']

        session = boto3.Session(aws_access_key_id=credentials['AccessKeyId'],
                                aws_secret_access_key=credentials['SecretAccessKey'],
                                aws_session_token=credentials['SessionToken'])
        return session