#!/usr/bin/env bash
# How to upload
./build.sh

docker push pyengine/aws-ec2:1.3
docker push spaceone/aws-ec2:1.3
