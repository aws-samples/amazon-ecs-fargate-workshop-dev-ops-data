---
title: "Lab 6: Update Task Definition"
date: 2020-04-10T11:10:13-06:00
weight: 85
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

### Review Task Def

#### Linux Capacities

Linux Capacities applies to what docker privileges the container has on a host. It is best practice to also apply least privilege what the commands the container can send docker. For example the the container should not need access to the logs, when logging to stderr and stdout docker will take care of this for the container. The container should not need access to edit the network, this is provided for the container. In this example we are dropping some of the most privileged capabilities.

    "linuxParameters": {
      "capabilities": {
        "drop": ["SYS_ADMIN","NET_ADMIN"]
        }
    }

Note that as of [ECS platform 1.4](https://aws.amazon.com/about-aws/whats-new/2020/04/aws-fargate-launches-platform-version-14/) you can enable `CAP_SYS_PTRACE` as well.
    
#### ulimits

Amazon ECS task definitions for Fargate support the ulimits parameter to define the resource limits to set for a container.

Fargate tasks use the default resource limit values with the exception of the nofile resource limit parameter, which Fargate overrides. 

You can also use ulimits to: 
- limit the number of services which can be run on the container
- limit the amount of resources which can be consumed by a container
- limit the number of open files that a container can use

In this example, we specify the nofile resource limit sets a restriction on the number of open files that a container can use. 
The default nofile soft limit is 1024 and hard limit is 4096 for Fargate tasks. These limits can be adjusted in a task definition if your tasks needs to handle a larger number of files.

    "ulimits": [
        {
            "name": "nofile",
            "softLimit": 1024,
            "hardLimit": 4096
        }
    ],

open `/app/index.html` and add some text to the body of the html to visualize changes made.

Push the changes to git

    git add .
    git commit -m "Update pipeline to tag container with build number"
    git push origin master

Wait for the container to be built and published in ECR. 

The commands above 
Deploy the updated container and task definition specifying fewer resources.

    aws ecs deploy --region $AWS_REGION --service 'fargate-dev-workshop-test'  \
     --cluster 'fargate-dev-workshop-test' --codedeploy-application 'fargate-dev-workshop-test' \
     --codedeploy-deployment-group 'ecs-fargate-workshop-test-dg' \
     --task-definition task-definition-test.json --codedeploy-appspec appsectest.json

In this lab reviewed some important security considerations which must be considered when running containers in production. It is not only important to be aware of what the containers has permission to do within AWS, but also what permissions the container has to the host and Docker. To properly secure containers you must apply security at all layers.
