---
title: "Lab 3: Deploy ECS Fargate Cluster"
date: 2020-04-10T11:10:05-06:00
weight: 55
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

#### Infrastructure Deployment

Before we deploy our VPC, ECS cluster, and service; enable CloudWatch container insights.
Container insights is a useful feature of CloudWatch, which allows you to gain insights of resource usage of your containers.
For more information on Container Insights see: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cloudwatch-container-insights.html

Running the following command will enable CloudWatch container insights by default for all ECS clusters which will be deployed into this AWS account.

    aws ecs put-account-setting --name "containerInsights" --value "enabled"
    
Now we will deploy Test Environment Stack

    cdk deploy ecs-inf-test
    
This stack will deploy the VPC, ECS Cluster, Load Balancer, and AutoScaling groups.

When the stack has finished deploying it should display the output of the load balancers url.
    
    ecs-inf-test.lburl = ecs-i-loadb-11111111-11111111.us-west-2.elb.amazonaws.com
    
Open a web browser and navigate to the load balancers url provided for your deployment.

In this lab we deployed the base infrastructure for the microservice. It is highly suggested to templatize the deployment of your environments. This will allow you to ensure that each of your environments is near identical and will reduce the errors which can be encountered due to unique or manual configuration. 
