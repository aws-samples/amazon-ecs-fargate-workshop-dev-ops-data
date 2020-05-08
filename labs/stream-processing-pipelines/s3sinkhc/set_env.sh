#!/bin/sh
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

set -x

JSON=$(/usr/bin/curl ${ECS_CONTAINER_METADATA_URI}/task)
echo $JSON
TASK=$(echo $JSON | /usr/local/bin/jq -r '.Containers[0].Networks[0].IPv4Addresses[0]')
echo $TASK

HEALTHCHECK_CONNECT_WORKER_ID=$TASK /usr/local/bin/kafka-connect-healthcheck
