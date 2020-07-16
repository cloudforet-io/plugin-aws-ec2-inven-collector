# -*- coding: utf-8 -*-
import logging

from spaceone.api.inventory.plugin import collector_pb2, collector_pb2_grpc
from spaceone.core.pygrpc import BaseAPI
from spaceone.core.pygrpc.message_type import *

_LOGGER = logging.getLogger(__name__)


class Collector(BaseAPI, collector_pb2_grpc.CollectorServicer):

    pb2 = collector_pb2
    pb2_grpc = collector_pb2_grpc

    def verify(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            data = collector_svc.verify(params)
            return self.locator.get_info('CollectorVerifyInfo', data)

    def collect(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            thread_resources = collector_svc.list_resources(params)

            for resources in thread_resources:
                for resource in resources:
                    res = {
                        'state': 'SUCCESS',
                        'message': '',
                        'resource_type': 'inventory.Server',
                        'match_rules': change_struct_type({'1': ['data.compute.instance_id']}),
                        # 'replace_rules': change_struct_type({}}),
                        'resource': change_struct_type(resource.to_primitive())
                    }

                    # _LOGGER.debug(f'[collect] Resource: {res}')
                    yield self.locator.get_info('ResourceInfo', res)
