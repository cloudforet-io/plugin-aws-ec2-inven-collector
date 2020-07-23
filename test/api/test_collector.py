import os
import unittest

from spaceone.core.unittest.runner import RichTestRunner
from spaceone.tester import TestCase, print_json

AKI = os.environ.get('AWS_ACCESS_KEY_ID', None)
SAK = os.environ.get('AWS_SECRET_ACCESS_KEY', None)

if AKI == None or SAK == None:
    print("""
##################################################
# ERROR 
#
# Configure your AWS credential first for test
##################################################
example)

export AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY_ID>
export AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_ACCESS_KEY>

""")
    exit

class TestCollector(TestCase):

    def test_init(self):
        v_info = self.inventory.Collector.init({'options': {}})
        print_json(v_info)


    def test_verify(self):
        options = {
        }
        secret_data = {
            'aws_access_key_id': AKI,
            'aws_secret_access_key': SAK
        }
        v_info = self.inventory.Collector.verify({'options': options, 'secret_data': secret_data})
        print_json(v_info)

    def test_collect(self):
        options = {}
        secret_data = {
            'aws_access_key_id': AKI,
            'aws_secret_access_key': SAK,
        }
        filter = {}

        resource_stream = self.inventory.Collector.collect({'options': options, 'secret_data': secret_data,
                                                            'filter': filter})
        # print(resource_stream)

        for res in resource_stream:
            print_json(res)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
