# Developer instruction

This document is for plugin developer or testing aws-ec2 plugin only.

You can run aws-ec2 collector server alone, then make a request for collect.

# Install

~~~bash
git clone https://github.com/spaceone-dev/plugin-aws-ec2.git
cd plugin-aws-ec2
export AWS_ACCESS_KEY_ID=<PUT YOUR AWS ACCESS_KEY>
export AWS_SECRET_ACCESS_KEY=<PUT YOUR AWS SECRET_ACCESS_KEY>

make test
~~~

After executing commands, this script builds aws-ec2-plugin and run as docker.
Then executing integration test.

Three test-cases should be **SUCCESS** like

~~~
test_collect                            test_collector.TestCollector               SUCCESS            9.421953
{'metadata': {'filter_format': [{'change_rules': [{'change_key': 'instance_id',
                                                   'resource_key': 'data.compute.instance_id'},
                                                  {'change_key': 'region_name',
                                                   'resource_key': 'data.compute.region'}],
                                 'key': 'project_id',
                                 'name': 'Project ID',
                                 'resource_type': 'SERVER',
                                 'search_key': 'identity.Project.project_id',
                                 'type': 'str'},
                                {'change_rules': [{'change_key': 'instance_id',
                                                   'resource_key': 'data.compute.instance_id'},
                                                  {'change_key': 'region_name',
                                                   'resource_key': 'data.compute.region'}],
                                 'key': 'collection_info.service_accounts',
                                 'name': 'Service Account ID',
                                 'resource_type': 'SERVER',
                                 'search_key': 'identity.ServiceAccount.service_account_id',
                                 'type': 'str'},
                                {'change_rules': [{'change_key': 'instance_id',
                                                   'resource_key': 'data.compute.instance_id'},
                                                  {'change_key': 'region_name',
                                                   'resource_key': 'data.compute.region'}],
                                 'key': 'server_id',
                                 'name': 'Server ID',
                                 'resource_type': 'SERVER',
                                 'search_key': 'inventory.Server.server_id',
                                 'type': 'list'},
                                {'key': 'instance_id',
                                 'name': 'Instance ID',
                                 'resource_type': 'CUSTOM',
                                 'type': 'list'},
                                {'key': 'region_name',
                                 'name': 'Region',
                                 'resource_type': 'CUSTOM',
                                 'type': 'list'}],
              'supported_resource_type': ['inventory.Server',
                                          'inventory.Region']}}

test_init                               test_collector.TestCollector               SUCCESS            0.011644
{}

test_verify                             test_collector.TestCollector               SUCCESS            0.374855

----------------------------------------------------------------------
Ran 3 tests in 9.840s

OK
~~~

