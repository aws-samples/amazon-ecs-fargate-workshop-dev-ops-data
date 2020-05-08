# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

#!/bin/bash
set -x

JSON=$(curl ${ECS_CONTAINER_METADATA_URI}/task)
echo $JSON
TASK=$(echo $JSON | jq -r '.Containers[0].Networks[0].IPv4Addresses[0]')
echo $TASK

BROKER_ARN=$(aws servicediscovery discover-instances --region $REGION --namespace-name FargateWorkshopNamespace --service-name $MSK_SERVICE | jq -r '.Instances[0].Attributes.broker_arn')
BOOTSTRAP_SERVERS=$(aws kafka get-bootstrap-brokers --region $REGION --cluster-arn $BROKER_ARN | jq -r '.BootstrapBrokerStringTls')
CONNECT_REST_ADVERTISED_HOST_NAME=$TASK CONNECT_BOOTSTRAP_SERVERS=$BOOTSTRAP_SERVERS /etc/confluent/docker/run
