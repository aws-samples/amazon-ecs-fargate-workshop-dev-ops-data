# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

#!/usr/bin/env python3

from aws_cdk import core
import os

from fargate_workshop_cdk.fargate_workshop_network_stack import *
from fargate_workshop_cdk.fargate_workshop_discovery_stack import *
from fargate_workshop_cdk.fargate_workshop_dataeng_stack import *
from fargate_workshop_cdk.fargate_workshop_dataeng_lambda import *
from fargate_workshop_cdk.fargate_workshop_dataeng_cluster import *
from fargate_workshop_cdk.fargate_workshop_dataeng_streams import *
from fargate_workshop_cdk.fargate_workshop_dataeng_s3sink import *
from fargate_workshop_cdk.fargate_workshop_dataeng_sftp import *
from fargate_workshop_cdk.fargate_workshop_dataeng_batch import *

app = core.App()
project = 'FargateWorkshop'

# Network stack is common
network = FargateWorkshopNetworkStack(app, "fargate-workshop-network", env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})
private_subnets = network.vpc.private_subnets
private_subnet_ids = [n.subnet_id for n in private_subnets]

# Start discovery stack
discovery = FargateWorkshopDiscoveryStack(app, "fargate-workshop-discovery", env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})

# Now build stacks for other tracks
dataeng = FargateWorkshopDataengStack(app, "fargate-workshop-dataeng", private_subnet_ids, network.vpc, network.default_vpc_cidr_block, project, discovery.namespace, env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})
FargateWorkshopDataengLambdaStack(app, "fargate-workshop-dataeng-lambda", dataeng.kafkaClientFirewall, vpc = network.vpc, kafkaCloudMap = dataeng.kafkaCloudMap, env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})
dataeng_cluster = FargateWorkshopDataengClusterStack(app, "fargate-workshop-dataeng-cluster", vpc = network.vpc, env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})
FargateWorkshopDataengStreamsStack(app, "fargat-workshop-dataeng-streams",  
        repo_arn = dataeng.docker_repo.repository_arn, 
        cluster = dataeng_cluster.cluster,
        repo = dataeng.docker_repo,
        clientFirewall = dataeng.unifiedClientFirewall,
        docdbClientFirewall = dataeng.clientFirewall,
        cmnamespace = dataeng.kafkaCloudMap.namespace.namespace_name,
        cmmsk = dataeng.kafkaCloudMap.service_name,
        cmddb = dataeng.docdbCloudMap.service_name,
        env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})
FargateWorkshopDataengS3SinkStack(app, "fargate-workshop-dataeng-kafkaconnect",  
        cluster = dataeng_cluster.cluster,
        kafkaClientFirewall = dataeng.unifiedClientFirewall,
        lbFirewall = dataeng.lbFirewall,
        kcrepo = dataeng.docker_repo_s3sink,
        hcrepo = dataeng.docker_repo_s3sinkhc,
        cmnamespace = dataeng.kafkaCloudMap.namespace.namespace_name,
        cmmsk = dataeng.kafkaCloudMap.service_name,
        vpc = network.vpc,
        env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})
FargateWorkshopDataengSftpStack(app, "fargate-workshop-dataeng-sfp",  
        cluster = dataeng_cluster.cluster,
        repo = dataeng.docker_repo_sftp,
        env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})
FargateWorkshopDataengBatchStack(app, "fargate-workshop-dataeng-batch",  
        cluster = dataeng_cluster.cluster,
        repo = dataeng.docker_repo_batch,
        env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})

app.synth()
