from spaceone.core.error import ERROR_BASE

class ERROR_PLUGIN_VERIFY_FAILED(ERROR_BASE):
    _message = '{plugin} failed to verify with {secret}'

class ERROR_VULNERABLE_PORTS(ERROR_BASE):
    _message = 'Vulnerable port option settings are incorrect. : {vulnerable_ports}'