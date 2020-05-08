# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_codepipeline as codepipeline,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_codepipeline_actions as actions,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_elasticloadbalancingv2 as elbv2,
    core
)


class FargateWorkshopDataengS3SinkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, cluster: ecs.ICluster, 
            kafkaClientFirewall: ec2.ISecurityGroup, 
            lbFirewall: ec2.ISecurityGroup, 
            kcrepo: ecr.IRepository,
            hcrepo: ecr.IRepository,
            cmnamespace: str,
            cmmsk: str,
            vpc: ec2.IVpc,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # S3 buckets
        self.kafkaConnectBucket = s3.Bucket(
                scope = self, 
                id = "KafkaConnectBucket", 
                block_public_access = s3.BlockPublicAccess.BLOCK_ALL,
                encryption = s3.BucketEncryption.S3_MANAGED
        )
        core.CfnOutput(
            scope = self, 
            id = "KafkaConnectBucketName",
            value=self.kafkaConnectBucket.bucket_name
        )

        # service skeleton
        kc_task_definition = ecs.FargateTaskDefinition(
                scope = self, 
                id = "KafkaConnectTaskDef",
                cpu=4096,
                memory_limit_mib=8192
        )
        kc_container = kc_task_definition.add_container(
                id = "KafkaConnectContainer",
                image=ecs.ContainerImage.from_ecr_repository(repository = kcrepo, tag = 'latest'),
                logging=ecs.LogDrivers.aws_logs(stream_prefix="KafkaConnect"),
                environment = {'CONNECT_PLUGIN_PATH': "/usr/share/java", 
                    'MSK_SERVICE': cmmsk, 
                    'CONNECT_GROUP_ID': 'KcS3SinkGroup',
                    'CONNECT_CONFIG_STORAGE_TOPIC': 'kc_config',
                    'CONNECT_OFFSET_STORAGE_TOPIC': 'kc_offset',
                    'CONNECT_STATUS_STORAGE_TOPIC': 'kc_status',
                    'CONNECT_VALUE_CONVERTER': 'org.apache.kafka.connect.storage.StringConverter',
                    'CONNECT_KEY_CONVERTER': 'org.apache.kafka.connect.storage.StringConverter',
                    'CONNECT_REST_PORT': '8083',
                    'CONNECT_CONSUMER_AUTO_OFFSET_RESET': 'latest',
                    'CONNECT_OFFSET_FLUSH_INTERVAL_MS': '120000',
                    'CONNECT_OFFSET_FLUSH_TIMEOUT_MS': '20000',
                    'CONNECT_INTERNAL_KEY_CONVERTER': 'org.apache.kafka.connect.json.JsonConverter',
                    'CONNECT_INTERNAL_VALUE_CONVERTER': 'org.apache.kafka.connect.json.JsonConverter',
                    'CONNECT_INTERNAL_KEY_CONVERTER_SCHEMAS_ENABLE': 'false',
                    'CONNECT_INTERNAL_VALUE_CONVERTER_SCHEMAS_ENABLE': 'false',
                    'CONNECT_SECURITY_PROTOCOL': 'SSL',
                    'CONNECT_CONSUMER_SECURITY_PROTOCOL': 'SSL',
                    'CONNECT_PRODUCER_SECURITY_PROTOCOL': 'SSL',
                    'REGION': self.region
                }
        )
        kc_container.add_port_mappings(ecs.PortMapping(container_port=8083, host_port=8083, protocol = ecs.Protocol.TCP))
        hc_container = kc_task_definition.add_container(
                id = "HealthCheckContainer",
                image=ecs.ContainerImage.from_ecr_repository(repository = hcrepo, tag = 'latest'),
                logging=ecs.LogDrivers.aws_logs(stream_prefix="KafkaConnectHc")
        )
        hc_container.add_port_mappings(ecs.PortMapping(container_port=18083, host_port=18083, protocol = ecs.Protocol.TCP))
        kc_task_definition.add_to_task_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['servicediscovery:DiscoverInstances']
                )
        )
        kc_task_definition.add_to_task_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['kafka:GetBootstrapBrokers']
                )
        )
        kc_task_definition.add_to_task_role_policy(
                statement = iam.PolicyStatement(
                    resources = [self.kafkaConnectBucket.bucket_arn, self.kafkaConnectBucket.bucket_arn + '/*'],
                    actions = ['s3:*']
                )
        )
        kc_svc = ecs.FargateService(
                scope = self, 
                id = "KafkaConnectSvc",
                task_definition=kc_task_definition,
                security_group = kafkaClientFirewall,
                cluster=cluster,
                desired_count=1
        )
        kc_scaling = kc_svc.auto_scale_task_count(max_capacity=10)
        kc_scaling.scale_on_cpu_utilization("CpuScaling",
            target_utilization_percent=70
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamS3SinkImageName',
                string_value = kc_container.container_name,
                parameter_name = 'image_s3sink'
        )
        ssm.StringParameter(
                scope = self,
                id = 'SSMParamS3SinkHCImageName',
                string_value = hc_container.container_name,
                parameter_name = 'image_s3sink_hc'
        )

        # Create ALB
        self.lb = elbv2.ApplicationLoadBalancer(
            self, "KafkaConnectALB",
            vpc=vpc,
            security_group = lbFirewall,
            internet_facing=False
        )
        listener = self.lb.add_listener(
            "KafkaConnectListener",
            port=8083,
            protocol = elbv2.ApplicationProtocol.HTTP,
            open=False
        )

        health_check = elbv2.HealthCheck(
            interval=core.Duration.seconds(120),
            path="/",
            port = '18083',
            timeout=core.Duration.seconds(60)
        )

        # Attach ALB to ECS Service
        listener.add_targets(
            "KafkaConnectSvcListener",
            port=8083,
            protocol = elbv2.ApplicationProtocol.HTTP,
            targets=[kc_svc],
            health_check=health_check,
        )
        core.CfnOutput(
            scope = self, 
            id = "KafkaConnectAlbDns",
            value=self.lb.load_balancer_dns_name
        )

        # pipeline
        self.cbproject = codebuild.PipelineProject(
                scope = self,
                id = 'KafkaS3SinkBuildImage',
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
                    resources = ['*'],
                    actions = ['ecr:*']
                )
        )
        self.pipeline = codepipeline.Pipeline(
                scope = self, 
                id = "KafkaS3Sink",
                pipeline_name = 'KafkaS3Sink'
        )
        self.pipeline.add_stage(
                stage_name='Source', 
                actions = [
                    actions.CodeCommitSourceAction(
                       repository = codecommit.Repository.from_repository_name(scope=self, id = 'FargateKcRepo', repository_name = 'FargateS3Sink'),
                       action_name = "Get-Code-Kc",
                       output = codepipeline.Artifact('code')
                   ),
                    actions.CodeCommitSourceAction(
                       repository = codecommit.Repository.from_repository_name(scope=self, id = 'FargateHcRepo', repository_name = 'FargateS3SinkHealthCheck'),
                       action_name = "Get-Code-Hc",
                       output = codepipeline.Artifact('codehc')
                   )
                ]
        )
        self.pipeline.add_stage(
                stage_name = 'Build',
                actions = [
                    actions.CodeBuildAction(
                        input = codepipeline.Artifact('code'),
                        extra_inputs = [codepipeline.Artifact('codehc')],
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
                        service = kc_svc,
                        input = codepipeline.Artifact('image'),
                        action_name = 'Deploy-Image'
                    )
                ]
        )
