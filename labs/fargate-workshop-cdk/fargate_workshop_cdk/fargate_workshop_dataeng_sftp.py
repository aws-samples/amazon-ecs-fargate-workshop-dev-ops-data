# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_codepipeline as codepipeline,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_codepipeline_actions as actions,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr as ecr,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_applicationautoscaling as applicationautoscaling,
    core
)


class FargateWorkshopDataengSftpStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, cluster: ecs.ICluster, repo: ecr.IRepository, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # service skeleton
        streamproc_task_definition = ecs_patterns.ScheduledFargateTask(
                scope = self, 
                id = "SftpTaskDef",
                cluster=cluster,
                desired_task_count=1,
                schedule = applicationautoscaling.Schedule.rate(duration = core.Duration.minutes(5)),
                scheduled_fargate_task_image_options = ecs_patterns.ScheduledFargateTaskImageOptions(
                    image=ecs.ContainerImage.from_ecr_repository(repository = repo, tag = 'latest'),
                    cpu=1024,
                    memory_limit_mib=2048
                )

        )
        streamproc_task_definition.task_definition.task_role.add_to_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['servicediscovery:DiscoverInstances', 'secretsmanager:Get*', 'ec2:Describe*']
                )
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamSftpImageName',
                string_value = streamproc_task_definition.task_definition.default_container.container_name,
                parameter_name = 'image_sftp'
        )
