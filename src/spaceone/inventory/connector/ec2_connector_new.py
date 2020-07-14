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
from spaceone.inventory.error import *
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

        for asg in paginator.get('LaunchConfigurations', []):
            launch_configurations.append(asg)

        return launch_configurations

    def list_launch_templates(self):
        pass

    def list_load_balancers(self):
        response = self.client.describe_load_balancers()

        return response

    def list_target_groups(self):
        response = self.client.describe_target_groups()

        return response

    def list_lb_listners(self):
        response = self.client.describe_listeners()

        return response

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