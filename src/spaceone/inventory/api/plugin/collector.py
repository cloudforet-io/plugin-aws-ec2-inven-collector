# -*- coding: utf-8 -*-
import logging

from spaceone.api.inventory.plugin import collector_pb2, collector_pb2_grpc
from spaceone.core.pygrpc import BaseAPI
from spaceone.core.pygrpc.message_type import *

_LOGGER = logging.getLogger(__name__)

class Collector(BaseAPI, collector_pb2_grpc.CollectorServicer):

    pb2 = collector_pb2
    pb2_grpc = collector_pb2_grpc

    def init(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            data = collector_svc.init(params)
            return self.locator.get_info('PluginInfo', data)


    def verify(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            data = collector_svc.verify(params)
            return self.locator.get_info('EmptyInfo')

    def collect(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            #response = ['i-1','i-2','i-3','i-4','i-5']
            resource_stream = collector_svc.list_resources(params)
            for resource in resource_stream:
                print(resource)

                res = {
                    'state': (resource['state']),
                    'message': '',
                    'resource_type': (resource['resource_type']),
                    'match_rules': change_struct_type(resource['match_rules']),
                    'replace_rules': change_struct_type(resource['replace_rules']),
                    'resource': change_struct_type(resource['resource'])

                }
                #print(res)
                _LOGGER.debug(f'[collect] Resource: {res}')
                yield self.locator.get_info('ResourceInfo', res)


            #resource_info = collector_svc.collect(params)
            #yield self.locator.get_info('ResourceInfo', resource_info)
