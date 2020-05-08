# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from aws_cdk import (
    aws_codebuild,
    core,
)

class genericBuild(core.Construct):
    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.Project = aws_codebuild.PipelineProject(
            self,
            id=id,
            project_name=id,
            environment = aws_codebuild.BuildEnvironment(
                build_image=aws_codebuild.LinuxBuildImage.STANDARD_2_0,
                compute_type=aws_codebuild.ComputeType.MEDIUM
            )
        )
