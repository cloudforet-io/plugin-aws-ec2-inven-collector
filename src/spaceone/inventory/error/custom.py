# -*- coding: utf-8 -*-

from spaceone.core.error import ERROR_BASE

class ERROR_PLUGIN_VERIFY_FAILED(ERROR_BASE):
    _message = '{plugin} failed to verify with {secret}'

