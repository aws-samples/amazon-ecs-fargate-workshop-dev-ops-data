# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    core
)


class FargateWorkshopOpsFrontend(core.Stack):

    def __init__(self, scope: core.Stack, id: str, cluster: ecs.ICluster, vpc, sec_group, desired_service_count, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.cluster = cluster
        self.vpc = vpc
        self.sec_group = sec_group
        self.desired_service_count = desired_service_count

        self.fargate_load_balanced_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "FrontendFargateLBService",
            cluster=self.cluster,
            desired_count=self.desired_service_count,
            service_name="Fargate-Frontend",
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

        self.fargate_load_balanced_service.service.connections.security_groups[0].add_ingress_rule(
            peer = ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection = ec2.Port.tcp(3000),
            description="Allow http inbound from VPC"
        )

        self.sec_grp_ingress_backend_to_frontend_3000 = ec2.CfnSecurityGroupIngress(
            self, "InboundBackendSecGrp3000",
            ip_protocol='TCP',
            source_security_group_id=self.fargate_load_balanced_service.service.connections.security_groups[0].security_group_id,
            from_port=3000,
            to_port=3000,
            group_id=self.sec_group.security_group_id
        )

        self.sec_grp_ingress_frontend_to_backend_3000 = ec2.CfnSecurityGroupIngress(
            self, "InboundFrontendtoBackendSecGrp3000",
            ip_protocol='TCP',
            source_security_group_id=self.sec_group.security_group_id,
            from_port=3000,
            to_port=3000,
            group_id=self.fargate_load_balanced_service.service.connections.security_groups[0].security_group_id,
        )    

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

        core.CfnOutput(
            self, "LoadBalancerDNS",
            value = self.fargate_load_balanced_service.load_balancer.load_balancer_dns_name
        )
