---
title: "Lab 5: Container Observability"
date: 2020-04-10T11:10:10-06:00
weight: 75
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

#### deploy Cloudformation to create some traffic. replace the `ParameterValue` with your specific load balancer.

    aws cloudformation create-stack --stack-name ecs-fargate-workshop-traffic \
        --template-body file://./r53_health_check.yaml \
        --parameters  ParameterKey=url,ParameterValue="<YOUR LOAD BALANCE URL>"
        
Navigate to the CloudWatch console.

Near the top left of the page where the `Overview` drop down menu is, select `Container Insights`.

In the drop down menu under Container Insights, take a look at the different metrics captured by ECS Service, ECS Cluster, and ECS Task.

Since we are using Fargate to host our workload there will be no data displayed for ECS instances.

You are able to select a time frame from the graphs and also view the container logs from the time you specified. For the container we previously deployed are underutilized. 

Run the following commands to deploy a smaller size container:

    sed -i '/cpu/c\   \"cpu\" : \"256\",' ./configs/task-definition-test.json
    sed -i '/memory/c\   \"memory\" : \"512\",' /configs/task-definition-test.json
    sed -i '/image/c\   \"image\" : \"YOUR-CONTAINER-REPO:BUILD-GUID\",' /configs/task-definition-test.json 

In this lab we have walked through the CloudWatch console and the Container Insights feature. Container Insights is a useful tool to right size your containers. If running your workloads are running on EC2 back compute, Container Insights can assist in being cost-conscious and right sizing your compute nodes.
