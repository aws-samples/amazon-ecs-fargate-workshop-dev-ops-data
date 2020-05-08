# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

#!/usr/bin/env python3

from aws_cdk import core
import os

from fargate_ops_cdk.fargate_workshop_ops_stack import *
from fargate_ops_cdk.fargate_workshop_ops_cluster import *
from fargate_ops_cdk.fargate_workshop_ops_frontend import *
from fargate_ops_cdk.fargate_workshop_ops_node_backend import *
from fargate_ops_cdk.fargate_workshop_ops_crystal_backend import *
from fargate_ops_cdk.fargate_workshop_ops_failed import *

class FargateDemo(core.App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.stack_name = "FargateWorkshopOps"

        self.base_module = FargateWorkshopOpsStack(self, self.stack_name + "-base", 
                                           env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})

        self.ops_cluster = FargateWorkshopOpsCluster(self, self.stack_name + "-cluster",
                                           vpc = self.base_module.vpc, 
                                           env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})

        self.ops_cluster_frontend = FargateWorkshopOpsFrontend(self, self.stack_name + "-frontend",
                                           self.ops_cluster.cluster, self.base_module.vpc,
                                           self.base_module.services_3000_sec_group,
                                           desired_service_count=3, 
                                           env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})

        self.ops_cluster_frontend = FargateWorkshopOpsNodeBackend(self, self.stack_name + "-nodejs-backend",
                                           self.ops_cluster.cluster, self.base_module.vpc, self.base_module.vpc.private_subnets,
                                           self.base_module.services_3000_sec_group,
                                           desired_service_count=3,
                                           env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})

        self.ops_cluster_frontend = FargateWorkshopOpsCrystalBackend(self, self.stack_name + "-crystal-backend",
                                           self.ops_cluster.cluster, self.base_module.vpc, self.base_module.vpc.private_subnets,
                                           self.base_module.services_3000_sec_group,
                                           desired_service_count=3,
                                           env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})

        self.ops_cluster_frontend = FargateWorkshopOpsFailed(self, self.stack_name + "-failed",
                                           self.ops_cluster.cluster, self.base_module.vpc, self.base_module.vpc.private_subnets,
                                           self.base_module.services_3000_sec_group,
                                           desired_service_count=1,
                                           env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']})

if __name__ == '__main__':
    app = FargateDemo()
    app.synth()
