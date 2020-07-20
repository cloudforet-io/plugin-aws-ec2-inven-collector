# -*- coding: utf-8 -*-

__all__ = ['PluginInfo', 'ResourceInfo', 'CollectorVerifyInfo']

import functools
from spaceone.api.inventory.plugin import collector_pb2
from spaceone.core.pygrpc.message_type import *

def ResourceInfo(resource_dict):
    return collector_pb2.ResourceInfo(**resource_dict)

def PluginInfo(result):
    result['metadata'] = change_struct_type(result['metadata'])
    return collector_pb2.PluginInfo(**result)

def CollectorVerifyInfo(result):
    """ result
    {
     'options': {
        'a': 'b',
        ...
        'auth_type': 'google_oauth2'
    }
    """
    result['options'] = change_struct_type(result['options'])
    return collector_pb2.CollectorVerifyInfo(**result)
