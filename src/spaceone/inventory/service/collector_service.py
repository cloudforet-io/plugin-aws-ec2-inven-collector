# -*- coding: utf-8 -*-
import time
import logging
from spaceone.core.service import *
from multiprocessing import Pool
import concurrent.futures
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

SUPPORTED_RESOURCE_TYPE = ['SERVER']
NUMBER_OF_CONCURRENT = 20

@authentication_handler
class CollectorService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.collector_manager: CollectorManager = self.locator.get_manager('CollectorManager')

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

        # STEP 1
        # parameter setting
        mp_params = self.set_params_for_regions(params)

        with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_OF_CONCURRENT) as executor:
            print("[ EXECUTOR START ]")
            future_executors = []
            for mp_param in mp_params:
                future_executors.append(executor.submit(self.collector_manager.list_resources, mp_param))

            for future in concurrent.futures.as_completed(future_executors):
                yield future.result()

        # STEP 2
        # Multi processing
        # with Pool(NUMBER_OF_CONCURRENT) as pool:
        #     pool_results = pool.map(self.collector_manager.list_resources, mp_params)
        #
        #     for pool_result in pool_results:
        #         for result in pool_result:
        #             response = {
        #                 'state': 'SUCCESS',
        #                 'resource_type': 'inventory.Server',
        #                 'match_rules': {
        #                     '1': ['data.compute.instance_id']
        #                 },
        #                 # 'replace_rules': {},
        #                 "reference": {},
        #                 'resource': result.to_primitive()
        #             }
        #
        #             print("-----------------")
        #             print(response)
        #             print("-----------------")
        #
        #             yield response

        for _p in mp_params:
            results = self.collector_manager.list_resources(_p)

            for result in results:
                response = {
                    'state': 'SUCCESS',
                    'resource_type': 'inventory.Server',
                    'match_rules': {
                        '1': ['data.compute.instance_id']
                    },
                    # 'replace_rules': {},
                    "reference": {},
                    'resource': result.to_primitive()
                }

                # print("-----------------")
                # print(response)
                # print("-----------------")

                yield response

        print(f'############## TOTAL FINISHED {time.time() - start_time} Sec ##################')

    def set_params_for_regions(self, params):
        params_for_regions = []

        (query, instance_ids, region_name) = self._check_query(params['filter'])
        query.append({'Name': 'instance-state-name', 'Values': ['running', 'shutting-down', 'stopping', 'stopped']})

        target_regions = self.get_all_regions(params['secret_data'], region_name)

        for target_region in target_regions:
            params_for_regions.append({
                'region_name': target_region,
                'query': query,
                'secret_data': params['secret_data'],
                'instance_ids': instance_ids
            })

        return params_for_regions

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

    def get_all_regions(self, secret_data, region_name):
        """ Find all region name
        Args:
            secret_data: secret data
            region_name (list): list of region_name if wanted

        Returns: list of region name
        """

        if 'region_name' in secret_data:
            return [secret_data['region_name']]

        if len(region_name) > 0:
            return region_name

        regions = self.collector_manager.list_regions(secret_data, DEFAULT_REGION)
        return [region.get('RegionName') for region in regions if region.get('RegionName') is not None]
