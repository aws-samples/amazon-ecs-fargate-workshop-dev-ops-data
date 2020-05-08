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
    aws_s3 as s3,
    core
)


class FargateWorkshopDataengBatchStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, cluster: ecs.ICluster, repo: ecr.IRepository, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # bucket
        self.xmlBucket = s3.Bucket(
                scope = self, 
                id = "XmlBucket", 
                block_public_access = s3.BlockPublicAccess.BLOCK_ALL,
                encryption = s3.BucketEncryption.S3_MANAGED
        )
        core.CfnOutput(
            scope = self, 
            id = "XmlBucketName",
            value=self.xmlBucket.bucket_name
        )

        # service skeleton
        batch_task_definition = ecs.FargateTaskDefinition(
                scope = self, 
                id = "BatchTaskDef",
                cpu=2048,
                memory_limit_mib=4096,
                volumes = [ecs.Volume(name='storage')]
        )
        batch_container = batch_task_definition.add_container(
                id = "BatchContainer",
                image=ecs.ContainerImage.from_ecr_repository(repository = repo, tag = 'latest'),
                logging=ecs.LogDrivers.aws_logs(stream_prefix="BatchProcessing"),
                environment = {'BUCKET': self.xmlBucket.bucket_name }
        )
        batch_container.add_mount_points(ecs.MountPoint(container_path = '/opt/data', read_only = False, source_volume = 'storage'))
        batch_task_definition.task_role.add_to_policy(
                statement = iam.PolicyStatement(
                    resources = [self.xmlBucket.bucket_arn, self.xmlBucket.bucket_arn + '/*'],
                    actions = ['s3:*']
                )
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamBatchImageName',
                string_value = batch_container.container_name,
                parameter_name = 'image_batch'
        )

