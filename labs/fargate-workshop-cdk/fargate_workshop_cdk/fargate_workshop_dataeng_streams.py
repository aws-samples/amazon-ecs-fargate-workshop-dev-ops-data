# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_codepipeline as codepipeline,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_codepipeline_actions as actions,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    core
)


class FargateWorkshopDataengStreamsStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, repo_arn: str, cluster: ecs.ICluster, repo: ecr.IRepository, 
            clientFirewall: ec2.ISecurityGroup, 
            docdbClientFirewall: ec2.ISecurityGroup, 
            cmnamespace: str,
            cmmsk: str,
            cmddb: str,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # service skeleton
        streamproc_task_definition = ecs.FargateTaskDefinition(
                scope = self, 
                id = "StreamProcTaskDef",
                cpu=1024,
                memory_limit_mib=2048
        )
        streamproc_container = streamproc_task_definition.add_container(
                id = "StreamProcContainer",
                image=ecs.ContainerImage.from_ecr_repository(repository = repo, tag = 'latest'),
                logging=ecs.LogDrivers.aws_logs(stream_prefix="StreamProcessing"),
                environment = {'NAMESPACE': cmnamespace, 'MSK_SERVICE': cmmsk, 'TOPIC_NAME': 'MyTopic', 'DDB_SERVICE': cmddb},
        )
        streamproc_task_definition.add_to_task_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['servicediscovery:DiscoverInstances']
                )
        )
        streamproc_task_definition.add_to_task_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['kafka:GetBootstrapBrokers']
                )
        )
        streamproc_service = ecs.FargateService(
                scope = self, 
                id = "StreamProcessingService",
                task_definition=streamproc_task_definition,
                assign_public_ip = False,
                security_group = clientFirewall,
                cluster=cluster,
                desired_count = 1
        )
        streamproc_scaling = streamproc_service.auto_scale_task_count(max_capacity=10)
        streamproc_scaling.scale_on_cpu_utilization("CpuScaling",
            target_utilization_percent=70
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamStreamProcImageName',
                string_value = streamproc_container.container_name,
                parameter_name = 'image_streamproc'
        )

        # pipeline
        self.cbproject = codebuild.PipelineProject(
                scope = self,
                id = 'KafkaToDocdbBuildImage',
                cache = codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
                environment = codebuild.BuildEnvironment(
                    build_image = codebuild.LinuxBuildImage.UBUNTU_14_04_DOCKER_18_09_0,
                    privileged = True,
                    compute_type = codebuild.ComputeType.LARGE
                )
        )
        self.cbproject.add_to_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['ssm:GetParameters', 'ecr:GetAuthorizationToken']
                )
        )
        self.cbproject.add_to_role_policy(
                statement = iam.PolicyStatement(
                    resources = [repo_arn],
                    actions = ['ecr:*']
                )
        )
        self.pipeline = codepipeline.Pipeline(
                scope = self, 
                id = "KafkaToDocDb",
                pipeline_name = 'KafkaToDocdb'
        )
        self.pipeline.add_stage(
                stage_name='Source', 
                actions = [
                    actions.CodeCommitSourceAction(
                       repository = codecommit.Repository.from_repository_name(scope=self, id = 'FargateStreamProcessorRepo', repository_name = 'FargateStreamProcessor'),
                       action_name = "Get-Code",
                       output = codepipeline.Artifact('code')
                   )
                ]
        )
        self.pipeline.add_stage(
                stage_name = 'Build',
                actions = [
                    actions.CodeBuildAction(
                        input = codepipeline.Artifact('code'),
                        project = self.cbproject,
                        outputs = [codepipeline.Artifact('image')],
                        action_name = 'Build-Image'
                    )
                ]
        )
        self.pipeline.add_stage(
                stage_name = 'Deploy',
                actions = [
                    actions.EcsDeployAction(
                        service = streamproc_service,
                        input = codepipeline.Artifact('image'),
                        action_name = 'Deploy-Image'
                    )
                ]
        )

        core.CfnOutput(
            self, "IgnoredOutput",
            value=docdbClientFirewall.security_group_id
        )



