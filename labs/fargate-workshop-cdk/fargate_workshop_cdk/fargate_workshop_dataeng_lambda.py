# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
        aws_docdb as docdb,
        aws_msk as msk,
        aws_ec2 as ec2,
        aws_s3 as s3,
        aws_servicediscovery as cloudmap,
        aws_events as events,
        aws_lambda as lambda_,
        aws_events_targets as targets,
        aws_iam as iam,
        core
        )

class FargateWorkshopDataengLambdaStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, kafkaClientFirewall: ec2.ISecurityGroup, vpc: ec2.IVpc, kafkaCloudMap: cloudmap.Service, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        # Kafka data producer
        lambdaFn = lambda_.Function(
                self, "KafkaProducer",
                code=lambda_.AssetCode('fargate_workshop_cdk/function.zip'),
                handler="kafka-producer.main",
                timeout=core.Duration.seconds(300),
                runtime=lambda_.Runtime.PYTHON_3_7,
                description = 'Simple Kafka producer for Fargate workshop',
                environment = {'NAMESPACE': kafkaCloudMap.namespace.namespace_name, 'SERVICE': kafkaCloudMap.service_name, 'TOPIC_NAME': 'MyTopic'},
                memory_size = 512,
                security_group = kafkaClientFirewall,
                vpc = vpc
        )
        lambdaFn.add_to_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['servicediscovery:DiscoverInstances']
                )
        )
        lambdaFn.add_to_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['kafka:GetBootstrapBrokers']
                )
        )
        # Run every 5 minutes
        # See https://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-schedule-expressions.html
        rule = events.Rule(
            self, "Rule",
            schedule=events.Schedule.rate(
                duration = core.Duration.minutes(5),
            ),
        )
        rule.add_target(targets.LambdaFunction(lambdaFn))

