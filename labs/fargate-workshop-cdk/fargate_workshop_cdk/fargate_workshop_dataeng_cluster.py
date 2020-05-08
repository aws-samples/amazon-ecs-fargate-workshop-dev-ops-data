# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    core
)


class FargateWorkshopDataengClusterStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, vpc: ec2.IVpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Fargate cluster
        self.cluster = ecs.Cluster(
                scope = self,
                id = 'StreamProcessingCluster',
                vpc = vpc
        )




