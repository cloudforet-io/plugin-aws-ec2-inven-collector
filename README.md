<h1 align="center">AWS EC2 Instance Collector</h1>  

<br/>  
<div align="center" style="display:flex;">  
  <img width="245" src="https://spaceone-custom-assets.s3.ap-northeast-2.amazonaws.com/console-assets/icons/aws-cloudservice.svg">
  <p> 
    <br>
    <img alt="Version"  src="https://img.shields.io/badge/version-1.14.3-blue.svg?cacheSeconds=2592000"  />    
    <a href="https://www.apache.org/licenses/LICENSE-2.0"  target="_blank"><img alt="License: Apache 2.0"  src="https://img.shields.io/badge/License-Apache 2.0-yellow.svg" /></a> 
  </p> 
</div>    

**Plugin to collect EC2 information**

> SpaceONE's [plugin-aws-ec2-inven-collector](https://github.com/spaceone-dev/plugin-aws-ec2-inven-collector) is a convenient tool to get EC2 resources information from AWS.


Find us also at [Dockerhub](https://hub.docker.com/repository/docker/spaceone/plugin-aws-ec2-inven-collector)
> Latest stable version : 1.14.3

Please contact us if you need any further information. (<support@spaceone.dev>)

---

## AWS Service Endpoint (in use)

 There is an endpoints used to collect AWS resources information.
AWS endpoint is a URL consisting of a region and a service code. 
<pre>
https://ec2.[region-code].amazonaws.com
https://autoscaling.[region-code].amazonaws.com
https://elbv2.[region-code].amazonaws.com
</pre>

We use a lots of endpoints because we collect information from many regions.  

### Region list

Below is the AWS region information.
The regions we collect are not all regions supported by AWS. Exactly, we target the regions results returned by [describe_regions()](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_regions) of AWS ec2 client.

|No.|Region name|Region Code|
|---|------|---|
|1|US East (Ohio)|us-east-2|
|2|US East (N. Virginia)|us-east-1|
|3|US West (N. California)|us-west-1|
|4|US West (Oregon)|us-west-2|
|5|Asia Pacific (Mumbai)|ap-south-1|
|6|Asia Pacific (Osaka)|ap-northeast-3|
|7|Asia Pacific (Seoul)|ap-northeast-2|
|8|Asia Pacific (Singapore)|ap-southeast-1|
|9|Asia Pacific (Sydney)|ap-southeast-2|
|10|Asia Pacific (Tokyo)|ap-northeast-1|
|11|Canada (Central)|ca-central-1|
|12|Europe (Frankfurt)|eu-central-1|
|13|Europe (Ireland)|eu-west-1|
|14|Europe (London)|eu-west-2|
|15|Europe (Paris)|eu-west-3|
|16|Europe (Stockholm)|eu-north-1|
|17|South America (São Paulo)|sa-east-1|

---

### Service list

The following is a list of services being collected and service code information.

|No.|Service name|Service Code|
|---|------|---|
|1|EC2 Instance|AmazonEC2|

---
## Authentication Overview

Registered service account on SpaceONE must have certain permissions to collect cloud service data Please, set
authentication privilege for followings:

<pre>
<code>
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "autoscaling:Describe*",
                "ec2:Describe*",
                "elasticloadbalancing:Describe*"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
</code>
</pre>

---
## Secret Data Configuration

To use the EC2 Collector plugin, AWS authentication information is required. You can configure authentication information using the following methods.

### 1. General Access Key Method (Single Account)

This method is used when collecting resources within the same AWS account.

#### Secret Data Format:
```json
{
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY"
}
```

#### Setup Method:

1. **Create IAM User in AWS Console**
   - AWS Console → IAM → Users → Create User
   - Enter user name (e.g., spaceone-collector)
   - Select Access Key creation option

2. **Attach Managed Policy**
   - Select one of the managed policies provided by AWS:
     - `ReadOnlyAccess`: Read-only permissions for all AWS services
     - Or use custom policy that includes only necessary services

3. **Create Access Key**
   - IAM User → Security credentials → Create access key
   - Save Access Key ID and Secret Access Key in a secure location

### 2. Cross-Account Assume Role Method (Multi-Account)

This method is used when collecting resources from different AWS accounts.

#### Secret Data Format:
```json
{
    "aws_access_key_id": "SOURCE_ACCOUNT_ACCESS_KEY_ID",
    "aws_secret_access_key": "SOURCE_ACCOUNT_SECRET_ACCESS_KEY",
    "role_arn": "arn:aws:iam::TARGET_ACCOUNT_ID:role/ROLE_NAME",
    "external_id": "OPTIONAL_EXTERNAL_ID"
}
```

#### Setup Method:

**Source Account (Account that runs collection) Setup:**
1. **Create IAM User and Set Permissions**
   - AWS Console → IAM → Users → Create User
   - Enter user name (e.g., spaceone-cross-account-collector)
   - Create Access Key
   - Attach `ReadOnlyAccess` policy

**Target Account (Account whose resources will be collected) Setup:**
1. **Create Cross-Account Role**
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Principal": {
                   "AWS": "arn:aws:iam::SOURCE_ACCOUNT_ID:user/SOURCE_USER_NAME"
               },
               "Action": "sts:AssumeRole",
               "Condition": {
                   "StringEquals": {
                       "sts:ExternalId": "YOUR_EXTERNAL_ID"
                   }
               }
           }
       ]
   }
   ```

2. **Attach Managed Policy to Role**
   - Attach `ReadOnlyAccess` policy to the created Role
   - Or attach custom policy that includes only necessary services


---
## API List for collecting resources

### Boto3 info

* [describe_regions](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_regions)
* [describe_instances](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances)
* [describe_instance_types](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instance_types)
* [describe_instance_attribute](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instance_attribute)
* [describe_auto_scaling_groups](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.describe_auto_scaling_groups)
* [describe_launch_configurations](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/autoscaling.html#AutoScaling.Client.describe_launch_configurations)
* [describe_launch_templates](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_launch_templates)
* [describe_load_balancers](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.describe_load_balancers)
* [describe_target_groups](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.describe_target_groups)
* [describe_listeners](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.describe_listeners)
* [describe_target_health](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2.html#ElasticLoadBalancingv2.Client.describe_target_health)
* [describe_security_groups](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_security_groups)
* [describe_subnets](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_subnets)
* [describe_vpcs](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_vpcs)
* [describe_volumes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_volumes)
* [describe_images](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_images)
* [describe_addresses](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_addresses)
* [get_caller_identity](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html#STS.Client.get_caller_identity)
* [assume_role](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html#STS.Client.assume_role)

---

# Release Note

## Version 1.14.3
FIX BUG: [Links in Security Group do not work](https://github.com/cloudforet-io/plugin-aws-ec2-inven-collector/issues/11)

## Version 1.12.1
Remove region filter in secret_data. It is not used.

## Version 1.3.1
Support collect Large Capacity of EC2s (More than 2k) 
* Handling API 'rate exceeded'
* Default maximum number of retries has set to handle up to 10k APIs
