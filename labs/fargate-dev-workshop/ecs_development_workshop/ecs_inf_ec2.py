# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_autoscaling as autoscaling,
    core
)

class EcsDevClusterStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, vpc: ec2.IVpc,  **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Fargate cluster
        self.cluster = ecs.Cluster(
                scope = self,
                id = 'ecs-dev-cluster',
                cluster_name = 'ecs-dev-cluster',
                vpc = vpc
        )
        # Or add customized capacity. Be sure to start the Amazon ECS-optimized AMI.
        self.auto_scaling_group1 = autoscaling.AutoScalingGroup(self, "ASG1",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux(),
            update_type=autoscaling.UpdateType.REPLACING_UPDATE,
            # Or use Amazon ECS-Optimized Amazon Linux 2 AMI
            # machineImage: EcsOptimizedImage.amazonLinux2(),
            desired_capacity=3
        )
            
        self.auto_scaling_group2 = autoscaling.AutoScalingGroup(self, "ASG2",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux(),
            update_type=autoscaling.UpdateType.REPLACING_UPDATE,
            # Or use Amazon ECS-Optimized Amazon Linux 2 AMI
            # machineImage: EcsOptimizedImage.amazonLinux2(),
            desired_capacity=3
        )

        self.cluster.add_auto_scaling_group(self.auto_scaling_group1)
        self.cluster.add_auto_scaling_group(self.auto_scaling_group2)

        self.lb = elbv2.ApplicationLoadBalancer(
            self, "LB",
            vpc=vpc,
            internet_facing=True
        )

        self.listener1 = self.lb.add_listener("Listener1", port=80)
        self.listener1.add_targets("Target", port=80, targets=[self.auto_scaling_group1])
        self.listener1.connections.allow_default_port_from_any_ipv4("Open to the world")

        self.listener2 = self.lb.add_listener("Listener2", port=8080)
        self.listener2.add_targets("Target", port=8080, targets=[self.auto_scaling_group2])
        self.listener2.connections.allow_default_port_from_any_ipv4("Open to the world")

