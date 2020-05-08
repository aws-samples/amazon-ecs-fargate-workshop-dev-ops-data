# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from ecs_development_workshop.code_pipeline_configuration import ContainerPipelineConfiguration

from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ecs_patterns,
    aws_autoscaling as autoscaling,
    aws_cloudwatch,
    aws_elasticloadbalancingv2_targets as elbvs_targets,
    aws_logs as logs,
    core
)

import json
from django.http import JsonResponse

class EcsInfFargate(core.Stack):
    
    def __init__(self, scope: core.Construct, id: str, config: ContainerPipelineConfiguration, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        #VPC
        vpc = ec2.Vpc(self, "TheVPC",
            cidr ="10.0.0.0/16"
        )

        #IAM roles
        service_task_def_exe_role = iam.Role(self, "ServiceTaskDefExecutionRole",
            assumed_by = iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
        service_task_def_exe_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonECSTaskExecutionRolePolicy'))

        service_task_def_role = iam.Role(self,'ServiceTaskDefTaskRole',
            assumed_by = iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
 
        code_deploy_role = iam.Role(self, "CodeDeployRole",
            assumed_by = iam.ServicePrincipal('codedeploy.amazonaws.com')
        )
        code_deploy_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AWSCodeDeployRoleForECS'))

        # Fargate cluster
        cluster = ecs.Cluster(
            scope = self,
            id = "ecs-cluster",
            cluster_name = config.ProjectName + "-" + config.stage,
            vpc = vpc
        )

        load_balancer = elbv2.ApplicationLoadBalancer(
            self, "load_balancer",
            vpc=vpc,
            internet_facing=True
        )
        
        #Security Group
        service_sg = ec2.SecurityGroup(self, "service_sg",vpc=vpc)
        service_sg.connections.allow_from(load_balancer, ec2.Port.tcp(80));

        #ECR Repo
        image_repo = ecr.Repository.from_repository_name(self, "image_repo",
                repository_name = config.ProjectName
        )
        
        log_group = logs.LogGroup(self, "log_group",
            log_group_name= config.ProjectName + "-" + config.stage, 
            removal_policy=core.RemovalPolicy.DESTROY, 
            retention=None
        )
        
        #ECS Task Def
        fargate_task_definition = ecs.FargateTaskDefinition(
                scope = self, 
                id = "fargate_task_definition",
                cpu=256,
                memory_limit_mib=512,
                execution_role = service_task_def_exe_role,
                task_role = service_task_def_role,
                family = config.ProjectName + "-" + config.stage
        )
        
        container = fargate_task_definition.add_container(
            id = "fargate_task_container",
            image=ecs.ContainerImage.from_ecr_repository(repository = image_repo, tag = 'release')
        )
        
        container.add_port_mappings(ecs.PortMapping(container_port=80, host_port=80, protocol = ecs.Protocol.TCP))
        
        #ECS Fargate Service
        fargate_service = ecs.FargateService(
            scope = self, 
            id = "fargate_service",
            security_group = service_sg,
            cluster=cluster,
            desired_count=5,
            deployment_controller = ecs.DeploymentController(type = ecs.DeploymentControllerType.CODE_DEPLOY),
            task_definition = fargate_task_definition,
            service_name = config.ProjectName + "-" + config.stage
        )
        
        #Main Env
        listern_health_check_main = elbv2.HealthCheck(
            healthy_http_codes = '200',
            interval = core.Duration.seconds(5),
            healthy_threshold_count = 2,
            unhealthy_threshold_count = 3,
            timeout = core.Duration.seconds(4)
        )
        #Test Env
        listern_health_check_test = elbv2.HealthCheck(
            healthy_http_codes = '200',
            interval = core.Duration.seconds(5),
            healthy_threshold_count = 2,
            unhealthy_threshold_count = 3,
            timeout = core.Duration.seconds(4)
        )
        
        listener_main = load_balancer.add_listener("load_balancer_listener_1", 
            port = 80,
        )

        listern_main_targets = listener_main.add_targets("load_balancer_target_1", port=80, 
            health_check = listern_health_check_main,
            targets=[fargate_service]
        )
        
        listener_test = load_balancer.add_listener("load_balancer_listener_2", 
            port = 8080,
        )
        
        listern_test_targets = listener_test.add_targets("load_balancer_target_2", port=80,  
            health_check = listern_health_check_test,
            targets=[fargate_service]
        )

        #Alarms: monitor 500s on target group
        aws_cloudwatch.Alarm(self,"TargetGroup5xx",
            metric = listern_main_targets.metric_http_code_target(elbv2.HttpCodeTarget.TARGET_5XX_COUNT),
            threshold = 1,
            evaluation_periods = 1,
            period = core.Duration.minutes(1)
        )
        
        aws_cloudwatch.Alarm(self,"TargetGroup25xx",
            metric = listern_test_targets.metric_http_code_target(elbv2.HttpCodeTarget.TARGET_5XX_COUNT),
            threshold = 1,
            evaluation_periods = 1,
            period = core.Duration.minutes(1)       
        )
        
        #Alarms: monitor unhealthy hosts on target group
        aws_cloudwatch.Alarm(self,"TargetGroupUnhealthyHosts",
            metric = listern_main_targets.metric('UnHealthyHostCount'),
            threshold = 1,
            evaluation_periods = 1,
            period = core.Duration.minutes(1)        
        )
        
        aws_cloudwatch.Alarm(self,"TargetGroup2UnhealthyHosts",
            metric = listern_test_targets.metric('UnHealthyHostCount'),
            threshold = 1,
            evaluation_periods = 1,
            period = core.Duration.minutes(1)        
        )

        core.CfnOutput(self,"lburl",
            value = load_balancer.load_balancer_dns_name,
            export_name = "LoadBalancerUrl"
        )
