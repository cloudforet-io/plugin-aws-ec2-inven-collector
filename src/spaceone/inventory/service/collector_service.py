# -*- coding: utf-8 -*-
import time
import logging
import concurrent.futures

from spaceone.core.service import *
from spaceone.inventory.manager.collector_manager import CollectorManager

_LOGGER = logging.getLogger(__name__)
DEFAULT_REGION = 'us-east-1'
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

SUPPORTED_FEATURES = ['garbage_collection']
SUPPORTED_RESOURCE_TYPE = ['inventory.Server', 'inventory.Region', 'inventory.CloudServiceType']
SUPPORTED_SCHEDULES = ['hours']
NUMBER_OF_CONCURRENT = 20


@authentication_handler
class CollectorService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.collector_manager: CollectorManager = self.locator.get_manager('CollectorManager')

    @transaction
    @check_required(['options'])
    def init(self, params):
        """ init plugin by options
        """
        capability = {
            'filter_format': FILTER_FORMAT,
            'supported_resource_type': SUPPORTED_RESOURCE_TYPE,
            'supported_features': SUPPORTED_FEATURES,
            'supported_schedules': SUPPORTED_SCHEDULES
        }
        return {'metadata': capability}

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
        secret_data = params['secret_data']
        region_name = params.get('region_name', DEFAULT_REGION)
        active = manager.verify(secret_data, region_name)

        return {}

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

        start_time = time.time()
        # parameter setting for multi threading
        mp_params = self.set_params_for_regions(params)
        resource_regions = []
        collected_region_code = []

        server_resource_format = {'resource_type': 'inventory.Server',
                                  'match_rules': {'1': ['reference.resource_id']}}
        region_resource_format = {'resource_type': 'inventory.Region',
                                  'match_rules': {'1': ['region_code', 'provider']}}
        cloud_service_type_resource_format = {'resource_type': 'inventory.CloudServiceType',
                                              'match_rules': {'1': ['name', 'group', 'provider']}}

        for cloud_service_type in self.collector_manager.list_cloud_service_types():
            yield cloud_service_type, cloud_service_type_resource_format

        with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_OF_CONCURRENT) as executor:
            future_executors = []
            for mp_param in mp_params:
                future_executors.append(executor.submit(self.collector_manager.list_resources, mp_param))

            for future in concurrent.futures.as_completed(future_executors):
                try:
                    for result in future.result():
                        collected_region = self.collector_manager.get_region_from_result(result)

                        if collected_region is not None and collected_region.region_code not in collected_region_code:
                            resource_regions.append(collected_region)
                            collected_region_code.append(collected_region.region_code)

                        yield result, server_resource_format
                except Exception as e:
                    _LOGGER.error(f'failed to result {e}')

        for resource_region in resource_regions:
            yield resource_region, region_resource_format

        print(f'############## TOTAL FINISHED {time.time() - start_time} Sec ##################')

    def set_params_for_regions(self, params):
        params_for_regions = []

        (query, instance_ids, filter_region_name) = self._check_query(params['filter'])
        query.append({'Name': 'instance-state-name', 'Values': ['running', 'shutting-down', 'stopping', 'stopped']})

        target_regions = self.get_all_regions(params['secret_data'], filter_region_name)

        for target_region in target_regions:
            params_for_regions.append({
                'region_name': target_region,
                'query': query,
                'secret_data': params['secret_data'],
                'instance_ids': instance_ids
            })

        return params_for_regions

    def get_all_regions(self, secret_data, filter_region_name):
        """ Find all region name
        Args:
            secret_data: secret data
            region_name (list): list of region_name if wanted

        Returns: list of region name
        """

        if 'region_name' in secret_data:
            return [secret_data['region_name']]

        if filter_region_name:
            return filter_region_name

        regions = self.collector_manager.list_regions(secret_data, DEFAULT_REGION)
        return [region.get('RegionName') for region in regions if region.get('RegionName')]

    @staticmethod
    def _check_query(query):
        """
        Args:
            query (dict): example
                  {
                      'instance_id': ['i-123', 'i-2222', ...]
                      'instance_type': 'm4.xlarge',
                      'region_name': ['aaaa']
                  }
        If there is region_name in query, this indicates searching only these regions
        """

        instance_ids = []
        filters = []
        region_name = []
        for key, value in query.items():
            if key == 'instance_id' and isinstance(value, list):
                instance_ids = value

            elif key == 'region_name' and isinstance(value, list):
                region_name.extend(value)

            else:
                if not isinstance(value, list):
                    value = [value]

                if len(value):
                    filters.append({'Name': key, 'Values': value})

        return filters, instance_ids, region_name
