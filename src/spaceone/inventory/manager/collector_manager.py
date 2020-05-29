# -*- coding: utf-8 -*-

__all__ = ['CollectorManager']

import logging

from datetime import datetime

from spaceone.core import config
from spaceone.core.error import *
from spaceone.core.manager import BaseManager
import boto3

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

    def list_resources(self, options, secret_data, filters):
        # call ec2 connector

        connector = self.locator.get_connector('EC2Connector')
        connector.verify(options, secret_data)

        # make query, based on options, secret_data, filter
        query = filters

        return connector.collect_info(query, secret_data)

    # def _get_ec2_region_list(self, credentials):
    #     """
    #     cred(dict)
    #         - aws_access_key_id
    #         - aws_secret_access_key
    #         - ...
    #     """
    #     session = boto3.Session(aws_access_key_id=credentials['aws_access_key_id'],
    #                                 aws_secret_access_key=credentials['aws_secret_access_key'])
    #
    #     resource = session.client('ec2')
    #
    #
    #     response = resource.describe_regions()
    #     region_list = list()
    #     for region_name in response['Regions']:
    #         region_list.append(region_name["RegionName"])
    #
    #
    #
    #     return region_list
