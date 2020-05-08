---
title: "Lab 2: Deploy Cluster"
date: 2020-04-10T11:14:51-06:00
weight: 15
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

Start by reviewing contents of the frontend task definition in file labs/fargate-ops-cdk/fargate_ops_cdk/fargate_workshop_ops_frontend.py

    class FargateWorkshopOpsFrontend(core.Stack):
    <..>
        self.fargate_load_balanced_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "FrontendFargateLBService",
            cluster=self.cluster,
            desired_count=self.desired_service_count,
            cpu=256,
            memory_limit_mib=512,
            public_load_balancer=True,
            task_image_options={
                "image":  ecs.ContainerImage.from_registry("brentley/ecsdemo-frontend"),
                "container_port": 3000,
                "enable_logging": True,
                "environment":  {
                "CRYSTAL_URL": "http://ecsdemo-crystal.service:3000/crystal",
                "NODEJS_URL": "http://ecsdemo-nodejs.service:3000"
                }
            },
         )

Use of CDK simplifies instantiation of AWS services such as ECS Fargate. Using roughly 15 lines of Python code you can instantiate ECS Task (note task_image options describing image details, port mappings, logging setting and environment), Service as well as CPU and memory setting for frontend task.

## Note
For the lab environment we will use networking features provided by the awsvpc network mode that give Amazon ECS tasks the same networking properties as Amazon EC2 instances. When you use the awsvpc network mode in your task definitions, every task that is launched from that task definition gets its own elastic network interface (ENI) and a primary private IP address. The task networking feature simplifies container networking and gives you more control over how containerized applications communicate with each other and other services within your VPCs.

For information about the other available network modes for tasks, see [Network Mode](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html#network_mode).

Frontend service will utilize [Target Tracking](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-autoscaling-targettracking.html) autoscaling policy to increase or decrease the desired count of tasks in Amazon ECS service automatically.  For more information, see the [Application Auto Scaling User Guide](https://docs.aws.amazon.com/autoscaling/application/userguide/what-is-application-auto-scaling.html). 
Scroll down to review Auto Scaling setup in CDK. Please note minimum and maximum capacity as well as CPU Scaling target settings and cooldown timers.

        scaling = self.fargate_load_balanced_service.service.auto_scale_task_count(
            min_capacity=3,
            max_capacity=6
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=30,
            scale_in_cooldown=core.Duration.seconds(60),
            scale_out_cooldown=core.Duration.seconds(60),
        )


Execute deployment of following start with CDK
    cdk deploy FargateWorkshopOps-frontend


Open ALB endpoint to verify fontend application is up and running.
You can get ALB endpoint link using following command:


    aws cloudformation describe-stacks --stack-name FargateWorkshopOps-frontend --query "Stacks[0].Outputs[0].OutputValue

This is what we'll have after the deployment is complete:

* Frontend Application Load Balancer
* Rails frontend service with auto-scaling
* 3 frontend application replicas 

### ECS Container Insights 

CloudWatch Container Insights is used to collect, aggregate, and summarize metrics and logs from your containerized applications and microservices.  The metrics that Container Insights collects are available in CloudWatch automatic dashboards. You can analyze and troubleshoot container performance and logs data with CloudWatch Logs Insights. 

Identify cluster name usig AWS CLI :
    
    aws ecs list-clusters

Output will be similat to an example below. Select and copy ECS cluster name starting with "FargateWorkshopOps-cluster-OpsCluster"

    {
    "clusterArns": [
        "arn:aws:ecs:<region>:<account>:cluster/FargateWorkshopOps-cluster-OpsClusterXXXXXXXX-XXXXXXXXXXXX"
    ]
    }

Enable Container Insights for your cluster by executing (please subtitute cluster variable with your cluster name).

    aws ecs update-cluster-settings --cluster "FargateWorkshopOps-cluster-OpsClusterXXXXXXXX-XXXXXXXXXXXXX" --settings name=containerInsights,value=enabled

Navigate to CloudWatch console and select "Container Insights" dashboard. Select "ECS Services" to view metrics for frontend service.

Once you have enabled Container Insights deploy two distinct backend services using CDK. Frontend application will be able to access backend servides using CloudMap service catalog.

    cdk deploy FargateWorkshopOps-crystal-backend FargateWorkshopOps-nodejs-backend

Verify all components operational status by visitig ALB endpoint. You can get ALB endpoint using following command:

    aws cloudformation describe-stacks --stack-name FargateWorkshopOps-frontend --query "Stacks[0].Outputs[0].OutputValue" --output text

### ECS Firelens

FireLens allow Fargate users to direct container logs to storage and analytics tools without modifying deployment scripts, manually installing extra software or writing additional code. 

FireLens works with either [Fluent Bit](https://fluentbit.io/) or [Fluentd](https://www.fluentd.org/), which means that you can send logs to any destination supported by either of those open-source projects. 

You can now stream logs directly to Amazon CloudWatch, Amazon Kinesis Data Firehose destinations such as Amazon Elasticsearch, Amazon S3, Amazon Kinesis Data Streams and partner tools like   Datadog, Splunk, Sumo Logic and New Relic. Using Amazon ECS task definition parameters, you can select destinations and optionally define filters for additional control and FireLens will ingest logs to target destinations.

![Fire Lens Architecture](/images/FireLens.png)

The diagram above shows how FireLens works. Container standard out logs are sent to the FireLens container over a Unix socket via the Fluentd Docker Log Driver. The driver supports both tcp and Unix sockets; we chose Unix socket because it is the faster and more performant option. In addition, the FireLens container listens on a tcp socket for Fluent forward protocol messages– this allows you to tag and send logs from your application code using the Fluent Logger Libraries.

Start by reviewing contents of the NodeJS backend task definition in file labs/fargate-ops-cdk/fargate_ops_cdk/fargate_workshop_ops_node_backend.py

For this particular lab scenario we will use CloudWatch as a log destination. For more information visit Firelens documentation.

            self.task_definition.add_container(
            "BackendNodeServiceContainer",
            image=ecs.ContainerImage.from_registry("brentley/ecsdemo-nodejs"),
            logging=ecs.LogDrivers.firelens(
                options={
                    "Name": "cloudwatch",
                    "log_key": "log",
                    "region": "us-west-2",
                    "delivery_stream": "my-stream",
                    "log_group_name": "firelens-fluent-bit",
                    "auto_create_group": "true",
                    "log_stream_prefix": "from-fluent-bit"}
            )
        )

Open CloudWatch console and observe following dashboards : 

* CloudWatch -> Logs -> Log Groups -> firelens-fluent-bit

Navigate to ECS Console -> Task Definition and select latest revision of "FargateWorkshopOpsnodejs" backend task. Scroll down and verify Firelens sidecar container definition.

![FireLens Sidecar](/images/FireLens-sidecar.png)
