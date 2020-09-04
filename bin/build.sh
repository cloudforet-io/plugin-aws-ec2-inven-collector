#! /bin/bash
# Build a docker image
cd ..
docker build -t pyengine/aws-ec2 .
docker tag pyengine/aws-ec2 pyengine/aws-ec2:1.3
