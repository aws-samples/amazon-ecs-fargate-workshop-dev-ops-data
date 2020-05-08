---
title: "Lab 4: Service and Task Troubleshooting"
date: 2020-04-10T11:16:04-06:00
weight: 35
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

Troubleshooting problems with services, start with reviewing diagnostic information is the service event log.

* Open the Amazon ECS console at https://console.aws.amazon.com/ecs/.
* On the Clusters page, select the cluster in which your service resides.
* On the Cluster : clustername page, select the service to inspect.
* On the Service : servicename page, choose Events.

If you have trouble starting a task, your task might be stopping because of an error. For example, you run the task and the task displays a PENDING status and then disappears. You can view errors like this in the Amazon ECS console by displaying the stopped task and inspecting it for error messages.

To troubleshoot stopped tasks for errors follow the steps below.

* Open the Amazon ECS console at https://console.aws.amazon.com/ecs/.
* On the Clusters page, select the cluster in which your stopped task resides.
* On the Cluster : clustername page, choose Tasks.
In the Desired task status table header, choose Stopped, and then select the stopped task to inspect. The most recent stopped tasks are listed first.
* In the Details section, inspect the Stopped reason field to see the reason that the task was stopped.

Current environment should have all services and tasks running without issues. To simulate a task error deploy  Fargate service using following command.

    cdk deploy FargateWorkshopOps-failed

This service will provision and run a task where underlying container stays on for 60 seconds and then is terminated. Wait for 3-5 minutes for service to stabilize and review service events and container stop reason to verify status using ECS console.
