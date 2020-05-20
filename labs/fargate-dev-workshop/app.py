# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

#!/usr/bin/env python3

from aws_cdk import core
import os

from ecs_development_workshop.docker_build_to_ecr_pipeline import DockerBuildToEcrPipeline
from ecs_development_workshop.code_pipeline_configuration import ContainerPipelineConfiguration
from ecs_development_workshop.ecs_inf_fargate import EcsInfFargate

app = core.App()

#BootStrap Developer Pipeline
developerPipelineTest = ContainerPipelineConfiguration(
    projectName = "fargate-dev-workshop",
    stage = "test"
)

DockerBuildToEcrPipeline(
    app, 
    "pipeline-to-ecr", 
    config = developerPipelineTest,
    env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']}
)

EcsInfFargate(
    app, 
    "ecs-inf-test", 
    config = developerPipelineTest,
    env={'account': os.environ['CDK_DEFAULT_ACCOUNT'], 'region': os.environ['CDK_DEFAULT_REGION']}
)

app.synth()