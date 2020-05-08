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

class EcrDeployToEcs(core.Stack):

#    def __init__(self, scope: core.Construct, id: str, cluster: ecs.Cluster, asg_1: autoscaling.IAutoScalingGroup, asg_2: autoscaling.IAutoScalingGroup, lb: elbv2.IApplicationLoadBalancer, config: ContainerPipelineConfiguration, **kwargs) -> None:
#        super().__init__(scope, id, **kwargs)
#
    def __init__(self, scope: core.Construct, id: str, config: ContainerPipelineConfiguration, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        source_output = codepipeline.Artifact(
            artifact_name=config.ProjectName+"-SourceOutput"
        )

        base_image_output = codepipeline.Artifact(
            artifact_name='BaseImage'
        )
        
        #Container Repo
        image_repo = ecr.Repository.from_repository_name(self, "base-repo",
                repository_name = config.ProjectName
        )
        
        commit = aws_codecommit.Repository.from_repository_name(self,"commit",
             config.ProjectName +"-app-repo"
        )

        #pipeline = codepipeline.Pipeline(self, "MyPipeline",
        #    pipeline_name = config.ProjectName + "-ecr-to-ecs"
        #)

        docker_source_action = codepipeline_actions.EcrSourceAction(
          action_name = 'BaseImage',
          repository =  image_repo,
          image_tag =  'release',
          output = base_image_output,            
        )
        
        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name="CodeCommit",
            repository=commit,
            output=source_output
        )
        
        #docker code repo secret scan
        build_project = aws_codebuild.PipelineProject(
            self, "build_project",
        
            build_spec = aws_codebuild.BuildSpec.from_source_filename(filename = 'configs/buildspec_secrets.yml'),
            
            environment = aws_codebuild.BuildEnvironment(privileged=True,),
            # pass the ecr repo uri into the codebuild project so codebuild knows where to push
            environment_variables={
                'commituri': aws_codebuild.BuildEnvironmentVariable(
                    value=commit.repository_clone_url_http),
                'tag': aws_codebuild.BuildEnvironmentVariable(
                    value = config.ProjectName)
            },
            description='Pipeline for CodeBuild',
            timeout=core.Duration.minutes(60),
        )
        
        build_project.add_to_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = ['cloudformation:DescribeStackResources']
                )
        )
        
        build_project.add_to_role_policy(
                statement = iam.PolicyStatement(
                    resources = ['*'],
                    actions = [
                        'ecr:GetAuthorizationToken',
                        'ecr:BatchCheckLayerAvailability',
                        'ecr:GetDownloadUrlForLayer',
                        'ecr:GetRepositoryPolicy',
                        'ecr:DescribeRepositories',
                        'ecr:ListImages',
                        'ecr:DescribeImages',
                        'ecr:BatchGetImage',
                        'ecr:InitiateLayerUpload',
                        'ecr:UploadLayerPart',
                        'ecr:CompleteLayerUpload',
                        'ecr:PutImage'
                    ],
                )
        )

        build_artifact = codepipeline.Artifact('BuildArtifact')

        image_details_artifact = codepipeline.Artifact('ImageDetails')
        
        build_action = codepipeline_actions.CodeBuildAction(
            action_name = 'CodeBuild',
            project = build_project,
            input = source_output,
            extra_inputs = [base_image_output],
            outputs = [build_artifact, image_details_artifact]
        )
        
        #pipeline.add_stage(
        #    stage_name = 'Build',
        #    actions = [build_action],
        #)

        # Deploy
        #self.add_deploy_stage(pipeline, 'Test', build_artifact, image_details_artifact)
        #self.add_deploy_stage(pipeline, 'Prod', build_artifact, image_details_artifact)

 
