---
title: "Lab 3: Scaling and Security"
date: 2020-04-10T11:16:02-06:00
weight: 25
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

This lab will cover scaling and security of ECS Fargate deployment.
During initial deployment with CDK we have created a Target Tracking auto scaling policy.
List and review CloudWatch alarms which trigger scaling events.

    aws cloudwatch describe-alarms

Based on initial configuration events will be triggered based on following conditions :
* Scale UP      : CPUUtilization > 30 for 3 datapoints within 3 minutes
* Scale DOWN    : CPUUtilization < 27 for 15 datapoints within 15 minutes

To initiate scaling event we need to generate client traffic with following command

    ab -n 1000000 -c 10  http://`aws cloudformation describe-stacks --stack-name FargateWorkshopOps-frontend --query "Stacks[0].Outputs[0].OutputValue" --output text`/

Open CloudWatch console and observe following dashboards : 

* CloudWatch -> Containers Insight -> ECS Services
* CloudWatch -> ALARMS
* Amazon ECS -> Clusters -> FargateWorkshopOps-cluster-OpsCluster -> Service -> FargateWorkshopOps-frontend-FrontendFargateLBService -> Tasks

After 3 minutes you should see new tasks being instantiated to account for increased traffic.
