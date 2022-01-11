
# plugin-aws-ec2

![AWS Cloud Services](https://spaceone-custom-assets.s3.ap-northeast-2.amazonaws.com/console-assets/icons/aws-cloudservice.svg)
**Plugin to collect EC2 information**

> SpaceONE's [plugin-aws-ec2-inven-collector](https://github.com/spaceone-dev/plugin-aws-ec2-inven-collector) is a convenient tool to get EC2 resources information from AWS.


Find us also at [Dockerhub](https://hub.docker.com/repository/docker/spaceone/plugin-aws-ec2-inven-collector)
> Latest stable version : 1.13

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
                "elasticloadbalancing:Describe*",
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
</code>
</pre>


---

# Release Note

## Version 1.12.1
Remove region filter in secret_data. It is not used.

## Version 1.3.1
Support collect Large Capacity of EC2s (More than 2k) 
* Handling API 'rate exceeded'
* Default maximum number of retries has set to handle up to 10k APIs
