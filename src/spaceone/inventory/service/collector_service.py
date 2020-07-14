# -*- coding: utf-8 -*-

import logging

from spaceone.core.error import *
from spaceone.core.service import *
from spaceone.core.pygrpc.message_type import *

from spaceone.inventory.error import *
from spaceone.inventory.manager.collector_manager import CollectorManager

_LOGGER = logging.getLogger(__name__)

FILTER_FORMAT = [
    {
        'key': 'project_id',
        'name': 'Project ID',
        'type': 'str',
        'resource_type': 'SERVER',
        'search_key': 'identity.Project.project_id',
        'change_rules': [{
            'resource_key': 'data.compute.instance_id',
            'change_key': 'instance_id'
        }, {
            'resource_key': 'data.compute.region',
            'change_key': 'region_name'
        }]
    }, {
        'key': 'collection_info.service_accounts',
        'name': 'Service Account ID',
        'type': 'str',
        'resource_type': 'SERVER',
        'search_key': 'identity.ServiceAccount.service_account_id',
        'change_rules': [{
            'resource_key': 'data.compute.instance_id',
            'change_key': 'instance_id'
        }, {
            'resource_key': 'data.compute.region',
            'change_key': 'region_name'
        }]
    }, {
        'key': 'server_id',
        'name': 'Server ID',
        'type': 'list',
        'resource_type': 'SERVER',
        'search_key': 'inventory.Server.server_id',
        'change_rules': [{
            'resource_key': 'data.compute.instance_id',
            'change_key': 'instance_id'
        }, {
            'resource_key': 'data.compute.region',
            'change_key': 'region_name'
        }]
    }, {
        'key': 'instance_id',
        'name': 'Instance ID',
        'type': 'list',
        'resource_type': 'CUSTOM'
    },
    {
        'key': 'region_name',
        'name': 'Region',
        'type': 'list',
        'resource_type': 'CUSTOM'
    }
]


SUPPORTED_RESOURCE_TYPE = ['SERVER']

@authentication_handler
class CollectorService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)

    @transaction
    @check_required(['options','secret_data'])
    def verify(self, params):
        """ verify options capability
        Args:
            params
              - options
              - secret_data: may be empty dictionary

        Returns:

        Raises:
             ERROR_VERIFY_FAILED:
        """
        manager = self.locator.get_manager('CollectorManager')
        options = params['options']
        secret_data = params['secret_data']
        active = manager.verify(options, secret_data)
        _LOGGER.debug(active)
        capability = {
            'filter_format':FILTER_FORMAT,
            'supported_resource_type' : SUPPORTED_RESOURCE_TYPE
            }
        return {'options': capability}


    def discover_ec2(self):



    @transaction
    @check_required(['options','secret_data', 'filter'])
    def list_resources(self, params):
        """ Get quick list of resources

        Args:
            params:
                - options
                - secret_data
                - filter

        Returns: list of resources
        """
        manager = self.locator.get_manager('CollectorManager')
        options = params['options']
        secret_data = params['secret_data']
        filters = params['filter']


        # STEP 1
        # parameter setting

        # STEP 2
        # Multi processing
        with Pool(NUMBER_OF_CONCURRENT) as pool:
            result = pool.map(self.discover_ec2, params)

        # STEP 3
        # 취합 후 return

        return manager.list_resources(options, secret_data, filters)

