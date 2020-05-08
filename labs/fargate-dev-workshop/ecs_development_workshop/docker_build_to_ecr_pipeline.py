# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

from ecs_development_workshop.code_pipeline_configuration import ContainerPipelineConfiguration
#from ecs_development_workshop.code_pipeline_generic_build_project import genericBuild
from aws_cdk import (
    aws_codebuild,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_codecommit,
    aws_codedeploy,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_ecr as ecr,
    aws_events as events,
    aws_lambda as lambda_,
    aws_autoscaling as autoscaling,
    aws_events_targets as targets,
    aws_elasticloadbalancingv2 as elbv2,
    aws_cloudwatch as cloudwatch,
    core,
)

class DockerBuildToEcrPipeline(core.Stack):

#    def __init__(self, scope: core.Construct, id: str, cluster: ecs.Cluster, asg_1: autoscaling.IAutoScalingGroup, asg_2: autoscaling.IAutoScalingGroup, lb: elbv2.IApplicationLoadBalancer, config: ContainerPipelineConfiguration, **kwargs) -> None:
#        super().__init__(scope, id, **kwargs)
#
    def __init__(self, scope: core.Construct, id: str, config: ContainerPipelineConfiguration, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        sourceOutput = codepipeline.Artifact(
            artifact_name=config.ProjectName+"-SourceOutput"
        )
    
        #pipelineStages = []

        # create lambda function
        #self.function = lambda_.Function(
        #    self, "lambda_function",
        #    runtime=lambda_.Runtime.PYTHON_3_7,
        #    handler="pipeline_starter.handler",
        #    code=lambda_.AssetCode('ecs_development_workshop/pipeline_starter.zip')
        #)
        
        #Code Repo
        commit = aws_codecommit.Repository(
            self,
            config.ProjectName + "-apprepo",
            repository_name=config.ProjectName+"-app-repo"
        )

        #Container Repo
        self.docker_repo = ecr.Repository(
                scope = self, 
                id = config.ProjectName,
                removal_policy=core.RemovalPolicy.DESTROY,
                repository_name = config.ProjectName
        )
        
        pipeline = codepipeline.Pipeline(self, "MyPipeline",
            pipeline_name = config.ProjectName + "-commit-to-ecr"
        )
        
        source_output = codepipeline.Artifact()
        
        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name="CodeCommit",
            repository=commit,
            output=source_output
        )

        #docker file linting
        cb_docker_build_lint = aws_codebuild.PipelineProject(
            self, "DockerLint",
            project_name= config.ProjectName + "-docker-lint",
            build_spec=aws_codebuild.BuildSpec.from_source_filename(
                filename='configs/buildspec_lint.yml'),
            environment=aws_codebuild.BuildEnvironment(
                build_image=aws_codebuild.LinuxBuildImage.UBUNTU_14_04_NODEJS_10_1_0,
                privileged=True,
            ),
            # pass the ecr repo uri into the codebuild project so codebuild knows where to push
            environment_variables={
                'ecr': aws_codebuild.BuildEnvironmentVariable(
                    value=self.docker_repo.repository_uri),
                'project_name': aws_codebuild.BuildEnvironmentVariable(
                    value=config.ProjectName)
            },
            description='linting the container dockerfile for best practices',
            timeout=core.Duration.minutes(60),
        )
        

        #docker code repo secret scan
        cb_docker_build_secretscan = aws_codebuild.PipelineProject(
            self, "DockerSecretScan",
            project_name= config.ProjectName + "-docker-secretscan",
            build_spec=aws_codebuild.BuildSpec.from_source_filename(
                filename='configs/buildspec_secrets.yml'),
            environment=aws_codebuild.BuildEnvironment(
                privileged=True,
            ),
            # pass the ecr repo uri into the codebuild project so codebuild knows where to push
            environment_variables={
                'commituri': aws_codebuild.BuildEnvironmentVariable(
                    value=commit.repository_clone_url_http),
                'ecr': aws_codebuild.BuildEnvironmentVariable(
                    value=self.docker_repo.repository_uri),
                'project_name': aws_codebuild.BuildEnvironmentVariable(
                    value=config.ProjectName)
            },
            description='Scanning container for secrets',
            timeout=core.Duration.minutes(60),
        )
        
        cb_docker_build_secretscan.add_to_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['codecommit:*']
                )
        )
        
        #push to ecr repo
        cb_docker_build_push = aws_codebuild.PipelineProject(
            self, "DockerBuild",
            project_name= config.ProjectName + "-docker-build",
            build_spec=aws_codebuild.BuildSpec.from_source_filename(
                filename='configs/docker_build_base.yml'),
            environment=aws_codebuild.BuildEnvironment(
                privileged=True,
            ),
            # pass the ecr repo uri into the codebuild project so codebuild knows where to push
            environment_variables={
                'ecr': aws_codebuild.BuildEnvironmentVariable(
                    value=self.docker_repo.repository_uri),
                'tag': aws_codebuild.BuildEnvironmentVariable(
                    value="release"),
                'project_name': aws_codebuild.BuildEnvironmentVariable(
                    value=config.ProjectName)
            },
            description='Deploy to ECR',
            timeout=core.Duration.minutes(60),
        )
        
        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        pipeline.add_stage(
            stage_name='Lint',
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name='DockerLintImages',
                    input=source_output,
                    project= cb_docker_build_lint,
                    run_order=1,
                )
            ]
        )

        pipeline.add_stage(
            stage_name='SecretScan',
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name='DockerSecretScanImages',
                    input=source_output,
                    project= cb_docker_build_secretscan,
                    run_order=1,
                )
            ]
        )
        
        pipeline.add_stage(
            stage_name='Build',
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name='DockerBuildImages',
                    input=source_output,
                    project= cb_docker_build_push,
                    run_order=1,
                )
            ]
        )

        self.docker_repo.grant_pull_push(cb_docker_build_push)

