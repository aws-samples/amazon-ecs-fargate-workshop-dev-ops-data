---
title: "Lab 7: Clean Up"
date: 2020-04-10T11:10:15-06:00
weight: 95
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

Run these commands to clean up the resources in this lab:

    aws deploy delete-deployment-group --deployment-group-name 'ecs-fargate-workshop-test-dg' --application-name fargate-dev-workshop-test
    aws deploy delete-application --application-name fargate-dev-workshop-test
    aws cloudformation delete-stack --stack-name ecs-fargate-workshop-traffic
    cdk destroy ecs-inf-test
    cdk destroy pipeline-to-ecr
