# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_ec2 as ec2,
    core
)
import itertools


class FargateWorkshopNetworkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC with private and public subnets
        self.vpc = ec2.Vpc( self, "FargateVpc", max_azs=3)

        # import default VPC
        self.default_vpc = ec2.Vpc.from_lookup(self, "DefaultVPC",
            # This imports the default VPC but you can also
            # specify a 'vpcName' or 'tags'.
            is_default=True
        )
        self.default_vpc_cidr_block = '172.31.0.0/16'

        # peering connection
        self.peer = ec2.CfnVPCPeeringConnection(
                scope = self, 
                id = "VpcPeer",
                peer_vpc_id = self.default_vpc.vpc_id,
                vpc_id = self.vpc.vpc_id,
                peer_region = self.region
        )

        # routes
        ii = 0
        for subnet in itertools.chain(self.vpc.private_subnets,self.vpc.public_subnets):
            route = ec2.CfnRoute(self, 
                    "PeerRoute{0}".format(ii), 
                    route_table_id= subnet.route_table.route_table_id, 
                    destination_cidr_block= self.default_vpc_cidr_block, 
                    vpc_peering_connection_id= self.peer.ref 
            )
            ii = ii + 1
        subnet = self.default_vpc.public_subnets[0]
        route = ec2.CfnRoute(self, 
                "PeerRoute{0}".format(ii), 
                route_table_id= subnet.route_table.route_table_id, 
                destination_cidr_block= self.vpc.vpc_cidr_block, 
                vpc_peering_connection_id= self.peer.ref 
        )
