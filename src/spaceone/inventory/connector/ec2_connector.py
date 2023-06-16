__all__ = ["EC2Connector"]

import logging
import boto3
from boto3.session import Session
from botocore.config import Config

from spaceone.core.error import *
from spaceone.core import utils
from spaceone.core.connector import BaseConnector
from spaceone.inventory.conf.cloud_service_conf import *


_LOGGER = logging.getLogger(__name__)
DEFAULT_REGION = 'us-east-1'
RESOURCES = ['cloudformation', 'cloudwatch', 'dynamodb', 'ec2', 'glacier', 'iam', 'opsworks', 's3', 'sns', 'sqs']

PAGINATOR_MAX_ITEMS = 10000
PAGINATOR_PAGE_SIZE = 50

DEFAULT_API_RETRIES = 10


class EC2Connector(BaseConnector):

    def __init__(self, *args, **kwargs):
        self.session = None
        self.ec2_client = None
        self.asg_client = None
        self.elbv2_client = None

    def verify(self, secret_data, region_name):
        self.set_connect(secret_data, region_name)
        return "ACTIVE"

    def set_connect(self, secret_data, region_name, service="ec2"):
        session = self.get_session(secret_data, region_name)
        aws_conf = {'region_name': region_name}

        if service in RESOURCES:
            resource = session.resource(service, **aws_conf)
            client = resource.meta.client
        else:
            resource = None
            client = session.client(service, region_name=region_name, verify=BOTO3_HTTPS_VERIFIED)
        return client, resource

    def get_session(self, secret_data, region_name):
        params = {
            'aws_access_key_id': secret_data['aws_access_key_id'],
            'aws_secret_access_key': secret_data['aws_secret_access_key'],
            'region_name': region_name
        }

        session = Session(**params)

        # ASSUME ROLE
        if role_arn := secret_data.get('role_arn'):
            sts = session.client('sts', verify=BOTO3_HTTPS_VERIFIED)

            _assume_role_request = {
                'RoleArn': role_arn,
                'RoleSessionName': utils.generate_id('AssumeRoleSession'),
            }

            if external_id := secret_data.get('external_id'):
                _assume_role_request.update({'ExternalId': external_id})

            assume_role_object = sts.assume_role(**_assume_role_request)
            credentials = assume_role_object['Credentials']

            assume_role_params = {
                'aws_access_key_id': credentials['AccessKeyId'],
                'aws_secret_access_key': credentials['SecretAccessKey'],
                'region_name': region_name,
                'aws_session_token': credentials['SessionToken']
            }
            session = Session(**assume_role_params)

        return session

    def set_client(self, secret_data, region_name):
        config = Config(retries={'max_attempts': DEFAULT_API_RETRIES})

        self.session = self.get_session(secret_data, region_name)
        self.ec2_client = self.session.client('ec2', config=config, verify=BOTO3_HTTPS_VERIFIED)
        self.asg_client = self.session.client('autoscaling', config=config, verify=BOTO3_HTTPS_VERIFIED)
        self.elbv2_client = self.session.client('elbv2', config=config, verify=BOTO3_HTTPS_VERIFIED)

    def list_regions(self, **query):
        query = self._generate_query(is_paginate=False, **query)
        response = self.ec2_client.describe_regions(**query)
        return response['Regions']

    def list_instances(self, **query):
        ec2_instances = []
        query = self._generate_query(is_paginate=True, **query)
        query.update({'Filters': [{'Name': 'instance-state-name',
                                   'Values': ['pending', 'running', 'shutting-down', 'stopping', 'stopped']}]
                      })
        paginator = self.ec2_client.get_paginator('describe_instances')
        response_iterator = paginator.paginate(**query)
        account_id = ''
        for data in response_iterator:
            for reservation in data.get('Reservations', []):
                if account_id == '':
                    account_id = reservation.get('OwnerId')
                ec2_instances.extend(reservation.get('Instances', []))
        return ec2_instances, account_id

    def list_instance_types(self, **query):
        instance_types = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.ec2_client.get_paginator('describe_instance_types')
        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            instance_types.extend(data.get('InstanceTypes', []))

        return instance_types

    def list_instance_attribute(self, instance_id, **query):
        response = self.ec2_client.describe_instance_attribute(Attribute='disableApiTermination',
                                                               InstanceId=instance_id, **query)

        attribute = response.get('DisableApiTermination', {'Value': False})
        return attribute.get('Value')

    def list_auto_scaling_groups(self, **query):
        auto_scaling_groups = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.asg_client.get_paginator('describe_auto_scaling_groups')

        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            auto_scaling_groups.extend(data.get('AutoScalingGroups', []))

        return auto_scaling_groups

    def list_launch_configurations(self, **query):
        launch_configurations = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.asg_client.get_paginator('describe_launch_configurations')
        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            launch_configurations.extend(data.get('LaunchConfigurations', []))

        return launch_configurations

    def list_launch_templates(self, **query):
        launch_templates = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.asg_client.get_paginator('describe_launch_templates')
        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            launch_templates.extend(data.get('LaunchTemplates', []))

        return launch_templates

    def list_load_balancers(self, **query):
        load_balancers = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.elbv2_client.get_paginator('describe_load_balancers')
        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            load_balancers.extend(data.get('LoadBalancers', []))

        return load_balancers

    def list_target_groups(self, **query):
        target_groups = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.elbv2_client.get_paginator('describe_target_groups')
        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            target_groups.extend(data.get('TargetGroups', []))

        return target_groups

    def list_listeners(self, load_balancer_arn, **query):
        response = self.elbv2_client.describe_listeners(LoadBalancerArn=load_balancer_arn, **query)
        return response.get('Listeners', [])

    def list_target_health(self, target_group_arn, **query):
        response = self.elbv2_client.describe_target_health(TargetGroupArn=target_group_arn, **query)
        return response.get('TargetHealthDescriptions', [])

    def list_security_groups(self, **query):
        security_groups = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.ec2_client.get_paginator('describe_security_groups')
        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            security_groups.extend(data.get('SecurityGroups', []))

        return security_groups

    def list_subnets(self, **query):
        subnets = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.ec2_client.get_paginator('describe_subnets')
        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            subnets.extend(data.get('Subnets', []))

        return subnets

    def list_vpcs(self, **query):
        vpcs = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.ec2_client.get_paginator('describe_vpcs')
        response_iterator = paginator.paginate(**query)
        for data in response_iterator:
            vpcs.extend(data.get('Vpcs', []))

        return vpcs

    def list_volumes(self, **query):
        volumes = []
        query = self._generate_query(is_paginate=True, **query)
        paginator = self.ec2_client.get_paginator('describe_volumes')
        response_iterator = paginator.paginate(**query)

        for data in response_iterator:
            volumes.extend(data.get('Volumes', []))

        return volumes

    def list_images(self, **query):
        query = self._generate_query(is_paginate=False, **query)
        response = self.ec2_client.describe_images(**query)
        return response.get('Images', [])

    def list_elastic_ips(self, **query):
        query = self._generate_query(is_paginate=False, **query)
        response = self.ec2_client.describe_addresses(**query)
        return response.get('Addresses', [])

    def _check_secret_data(self, secret_data):
        if 'aws_access_key_id' not in secret_data:
            raise ERROR_REQUIRED_PARAMETER(key='secret.aws_access_key_id')

        if 'aws_secret_access_key' not in secret_data:
            raise ERROR_REQUIRED_PARAMETER(key='secret.aws_secret_access_key')

    def _create_session_with_access_key(self, aws_access_key_id, aws_secret_access_key):
        session = boto3.Session(aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key)

        sts = session.client('sts', verify=BOTO3_HTTPS_VERIFIED)
        sts.get_caller_identity()
        return session

    def _create_session_with_assume_role(self, aws_access_key_id, aws_secret_access_key, role_arn):
        session = self._create_session_with_access_key(aws_access_key_id, aws_secret_access_key)

        sts = session.client('sts', verify=BOTO3_HTTPS_VERIFIED)
        assume_role_object = sts.assume_role(RoleArn=role_arn, RoleSessionName=utils.generate_id('AssumeRoleSession'))
        credentials = assume_role_object['Credentials']

        session = boto3.Session(aws_access_key_id=credentials['AccessKeyId'],
                                aws_secret_access_key=credentials['SecretAccessKey'],
                                aws_session_token=credentials['SessionToken'])
        return session

    @staticmethod
    def _generate_query(is_paginate=False, **query):
        if is_paginate:
            query.update({
                'PaginationConfig': {
                    'MaxItems': PAGINATOR_MAX_ITEMS,
                    'PageSize': PAGINATOR_PAGE_SIZE,
                }
            })

        return query

