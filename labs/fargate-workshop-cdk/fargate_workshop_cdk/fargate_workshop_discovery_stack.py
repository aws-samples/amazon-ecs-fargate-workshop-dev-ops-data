# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_servicediscovery as cloudmap,
    core
)


class FargateWorkshopDiscoveryStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # CloudMap namespace
        self.namespace = cloudmap.HttpNamespace(
                scope = self,
                id = 'CloudMap',
                name = 'FargateWorkshopNamespace'
        )



