---
title: "Architecture"
date: 2020-04-10T11:07:37-06:00
weight: 25
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

For this workshop you will start with a basic CI/CD pipeline that builds and pushes a container image to an Amazon ECR repository.  As you work through the tasks in your latest sprint you'll end up with the CI/CD pipeline as shown below.  It will include stages within your AWS CodePipeline for linting Dockerfiles, scanning for secrets.  This will allow your developers to quickly fix and iterate on their code which will lead to faster and more secure deliveries. After we have pushed an image through the CI/CD pipeline we will begin to deploy the container to ECS. 

![Pipeline Architecture](/images/fargate-dev-lab.png)

Please use the **us-west-2** (Oregon) or **us-east-1** (Virgina) regions for this workshop.
