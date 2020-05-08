# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from code_pipeline_configuration import ContainerPipelineConfiguration
from code_pipeline_generic_build_project import genericBuild
from aws_cdk import (
    aws_codebuild,
    aws_codecommit,
    aws_codepipeline,
    aws_codepipeline_actions,
    core,
)


class CodePipelineGeneratorStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, config: ContainerPipelineConfiguration, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        sourceOutput = aws_codepipeline.Artifact(
            artifact_name=config.ProjectName+"-SourceOutput"
        )

        pipelineStages = []

        commit = aws_codecommit.Repository(
            self,
            config.ProjectName + "-codeRepo",
            repository_name=config.ProjectName+"-Repository"
        )
        pipelineStages.append(
            aws_codepipeline.StageOptions(
                stage_name="Source",
                actions=[
                    aws_codepipeline_actions.CodeCommitSourceAction(
                    action_name="Commit",
                    repository=commit,
                    output=sourceOutput
                )]
            )
        )

        build = genericBuild(self, config.ProjectName+"-Build")
        pipelineStages.append(
            aws_codepipeline.StageOptions(
                stage_name="Build",
                actions=[
                    aws_codepipeline_actions.CodeBuildAction(
                    action_name="Build",
                    project=build.Project,
                    input=sourceOutput
                )]
            )
        )

        if(config.AllTest or config.UnitTest):
            unitTest = genericBuild(self, config.ProjectName+"-UnitTests")
            pipelineStages[1].actions.append(
                aws_codepipeline_actions.CodeBuildAction(
                    action_name="UnitTests",
                    project=build.Project,
                    input=sourceOutput
                )
            )

        containerLinting=genericBuild(self, config.ProjectName+"-ContainerLinting")
        pipelineStages[1].actions.append(
            aws_codepipeline_actions.CodeBuildAction(
                action_name="Linting",
                project=build.Project,
                input=sourceOutput
            )
        )
        

        if(config.AllTest or config.IntegrationTests):
            integrationTest=genericBuild(
                self, config.ProjectName+"-IntegrationTests")

        if(config.AllTest or config.EndToEndTest):
            endToEnd=genericBuild(self, config.ProjectName+"-EndToEndTests")

        if(config.AllTest or config.LoadTest):
            loadTest=genericBuild(self, config.ProjectName+"-LoadTests")

        pipeline=aws_codepipeline.Pipeline(
            self,
            config.ProjectName+"-PipeLine",
            pipeline_name=config.ProjectName+"-Pipeline",
            stages=pipelineStages,
        )
