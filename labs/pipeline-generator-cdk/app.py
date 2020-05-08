# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

#!/usr/bin/env python3

from aws_cdk import core
from code_pipeline_generator.code_pipeline_generator_stack import CodePipelineGeneratorStack
from code_pipeline_generator.code_pipeline_configuration import ContainerPipelineConfiguration


app = core.App()

#BootStrap Developer Pipeline
developerPipeline = ContainerPipelineConfiguration(
    projectName = "Fargate-Developer"
)
CodePipelineGeneratorStack(app, "fargate-developerPipline",developerPipeline)

#Bootstrap Operations Pipeline
operationsPipeline = ContainerPipelineConfiguration(
    projectName = "Fargate-Operations",
    allTest=False
)
CodePipelineGeneratorStack(app,"fargate-operationsPipeline",operationsPipeline)
app.synth()
