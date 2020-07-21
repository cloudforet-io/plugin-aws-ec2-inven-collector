# -*- coding: utf-8 -*-
import logging

from spaceone.api.inventory.plugin import collector_pb2, collector_pb2_grpc
from spaceone.core.pygrpc import BaseAPI
from spaceone.core.pygrpc.message_type import *

_LOGGER = logging.getLogger(__name__)


class Collector(BaseAPI, collector_pb2_grpc.CollectorServicer):

    pb2 = collector_pb2
    pb2_grpc = collector_pb2_grpc
    # asdf
    def init(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            data = collector_svc.init(params)
            return self.locator.get_info('PluginInfo', data)

    def verify(self, request, context):
        params, metadata = self.parse_request(request, context)
    # ddd
        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            return self.locator.get_info('EmptyInfo')

    def collect(self, request, context):
        params, metadata = self.parse_request(request, context)
    # 111
        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            for resource in collector_svc.list_resources(params):
                res = {
                    'state': 'SUCCESS',
                    'message': '',
                    'resource_type': 'inventory.Server',
                    'match_rules': change_struct_type({'1': ['data.compute.instance_id']}),
                    # 'replace_rules': change_struct_type({}}),
                    'resource': change_struct_type(resource.to_primitive())
                }

                yield self.locator.get_info('ResourceInfo', res)
