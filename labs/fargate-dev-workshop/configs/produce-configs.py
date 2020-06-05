# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: MIT-0

import json 
import boto3
import sys

#command example
#python produce-configs.py fargate-dev-workshop test 11111111111.dkr.ecr.us-west-2.amazonaws.com/fargate-dev-workshop:9b2de43d-e787-4f1e-b9df-1eb73319fa4d


#stack prefix given by cdk app.py
stack_prefix = "ecs-inf-"

#input from cdk app.py
project_name = sys.argv[1] 

#input from cdk app.py
app_env =  sys.argv[2]

#input new ecs task def 
image = sys.argv[3]

#'ecs-inf-prod'
stack_name = stack_prefix + app_env

account_number = boto3.client('sts').get_caller_identity().get('Account')
region = boto3.client('sts').get_caller_identity().get('Region')

# create a boto3 client first
cloudformation = boto3.client('cloudformation', region_name='us-west-2')

inf_stack = cloudformation.describe_stack_resources(
    StackName=stack_name
)

stack_alarms = []

#Deployment Group Replacements
for stack in inf_stack['StackResources']:
    #ECS Cluster Name
    if("ecscluster" in stack['LogicalResourceId']):
        ecs_cluster = stack['PhysicalResourceId']

    if("servicesg" in stack['LogicalResourceId']):
        if( "sg-" in stack['PhysicalResourceId']):
            ecs_task_sg = stack['PhysicalResourceId']

    if("ServiceTaskDefExecutionRoleDefaultPolicy"in stack['LogicalResourceId']):
        ecs_task_exe_role_policy = stack['PhysicalResourceId']  
    elif("ServiceTaskDefExecutionRole" in stack['LogicalResourceId']):
        ecs_task_exe_role_arn = "arn:aws:iam::" + account_number + ":role/" + stack['PhysicalResourceId']

    if("ServiceTaskDefTaskRole" in stack['LogicalResourceId']):
        ecs_task_role_arn = "arn:aws:iam::" + account_number + ":role/" + stack['PhysicalResourceId']

    if("TheVPCPrivateSubnet1Subnet" in stack['LogicalResourceId']):
        ecs_private_subnet1 = stack['PhysicalResourceId']

    if("TheVPCPrivateSubnet2Subnet" in stack['LogicalResourceId']):
        ecs_private_subnet2 = stack['PhysicalResourceId']    

    if("ecsclusterLBPublicListenerECSGroup" in stack['LogicalResourceId']):
        ecs_cluster_public_listener = stack['PhysicalResourceId']

    if("CodeDeployRole" in stack['LogicalResourceId']):
        code_deploy_role = "arn:aws:iam::" + account_number + ":role/" + stack['PhysicalResourceId']
        
    if("loadbalancerloadbalancerlistener1loadbalancertarget1Group" in stack['LogicalResourceId']):
        load_balancer_listern_tg_arn1 = stack['PhysicalResourceId']
        load_balancer_listern_tg_name1 = stack['PhysicalResourceId'].split("/",1)[1].split("/",1)[0]
    elif("loadbalancerloadbalancerlistener1" in stack['LogicalResourceId']):
        load_balancer_listern_arn1 = stack['PhysicalResourceId']
        
    if("loadbalancerloadbalancerlistener2loadbalancertarget2Group" in stack['LogicalResourceId']):
        load_balancer_listern_tg_arn2 = stack['PhysicalResourceId'] 
        load_balancer_listern_tg_name2 = stack['PhysicalResourceId'].split("/",1)[1].split("/",1)[0]
    elif("loadbalancerloadbalancerlistener2" in stack['LogicalResourceId']):
        load_balancer_listern_arn2 = stack['PhysicalResourceId']
    
    if("TargetGroup25xx" in stack['LogicalResourceId']):
        stack_alarms.append({ "name": stack['PhysicalResourceId']})
    if("TargetGroup2UnhealthyHosts" in stack['LogicalResourceId']):
        stack_alarms.append({ "name": stack['PhysicalResourceId']})
    if("TargetGroup5xx" in stack['LogicalResourceId']):
        stack_alarms.append({ "name": stack['PhysicalResourceId']})
    if("TargetGroupUnhealthyHosts" in stack['LogicalResourceId']):
        stack_alarms.append({ "name": stack['PhysicalResourceId']})
        
 #edit deployment group
with open('./deployment-group.json', 'r') as deploy_group_file:
    json_data = json.load(deploy_group_file)
    json_data['ecsServices'][0]['clusterName'] = ecs_cluster
    json_data['ecsServices'][0]['serviceName'] = project_name + "-" + app_env
    json_data['loadBalancerInfo']['targetGroupPairInfoList'][0]['targetGroups'][0]['name'] = load_balancer_listern_tg_name1
    json_data['loadBalancerInfo']['targetGroupPairInfoList'][0]['targetGroups'][1]['name'] = load_balancer_listern_tg_name2
    json_data['loadBalancerInfo']['targetGroupPairInfoList'][0]['prodTrafficRoute']['listenerArns'] = [load_balancer_listern_arn1]
    json_data['loadBalancerInfo']['targetGroupPairInfoList'][0]['testTrafficRoute']['listenerArns'] = [load_balancer_listern_arn2]
    json_data['serviceRoleArn'] = code_deploy_role
    json_data['alarmConfiguration']['alarms'] = stack_alarms
    json_data['applicationName'] = project_name + "-" + app_env
with open('./deployment-group-' + app_env +'.json', 'w+') as file:
    json.dump(json_data, file, indent=2)    

#edit Service definition
with open('./service-definition.json', 'r') as file:
    json_data = json.load(file)
    json_data['cluster'] = ecs_cluster
    json_data['networkConfiguration']['awsvpcConfiguration']['securityGroups'] = [ecs_task_sg]
    json_data['networkConfiguration']['awsvpcConfiguration']['subnets'] = [ecs_private_subnet1,ecs_private_subnet2]
    json_data['taskDefinition'] = project_name + "-" + app_env
    json_data['loadBalancers'][0]['targetGroupArn'] = load_balancer_listern_tg_arn1
    json_data['loadBalancers'][0]['containerName'] = project_name + "-" + app_env
with open('./service-definition-' + app_env +'.json', 'w+') as file:
    json.dump(json_data, file, indent=2)  
    
#edit ecs definition
with open('./task-definition.json', 'r') as file:
    json_data = json.load(file)
    json_data['taskRoleArn'] = ecs_task_role_arn
    json_data['executionRoleArn'] = ecs_task_exe_role_arn
    json_data['family'] = project_name + '-' + app_env
    json_data['containerDefinitions'][0]['image'] = image
    json_data['containerDefinitions'][0]['name'] = project_name + "-" + app_env
    json_data['containerDefinitions'][0]['logConfiguration']['options']['awslogs-region'] = region
with open('./task-definition-' + app_env +'.json', 'w+') as file:
    json.dump(json_data, file, indent=2)  
   
#edit app sec
with open('./appspec.json', 'r') as file:
    json_data = json.load(file)
    json_data['Resources'][0]['TargetService']['Properties']['TaskDefinition'] = project_name + "-" + app_env
    json_data['Resources'][0]['TargetService']['Properties']['LoadBalancerInfo']['ContainerName'] = project_name + "-" + app_env
    json_data['Resources'][0]['TargetService']['Properties']['NetworkConfiguration']['awsvpcConfiguration']['subnets'] = [ecs_private_subnet1,ecs_private_subnet2]
    json_data['Resources'][0]['TargetService']['Properties']['NetworkConfiguration']['awsvpcConfiguration']['securityGroups'] = [ecs_task_sg]
with open('./appsec' + app_env +'.json', 'w+') as file:
    json.dump(json_data, file, indent=2)  
