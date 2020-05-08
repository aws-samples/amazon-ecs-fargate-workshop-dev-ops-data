---
title: "Lab 4: Blue Green Deploy"
date: 2020-04-10T11:10:09-06:00
weight: 65
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

In this lab you will update our container image and then deploy in a Blue / Green fashion.

Before you can do that, you will delete the service we just deployed.
Using the AWS console navigate to the ECS console select the cluster for the workshop.
Select the Service deployed and delete it
Go to Tasks, and stop all running tasks.

#### Navigate back configs

In your Cloud9 editor, open the file `/configs/docker_build_base.yml`.

Change the following
Before:

    - docker build -t $project_name:$tag .
    - docker tag $project_name:$tag $ecr:$tag
    - docker push $ecr

After:

    - docker build -t $project_name:$IMAGE_TAG .
    - docker tag $project_name:$IMAGE_TAG $ecr:$IMAGE_TAG
    - docker push $ecr
    
These changes will modify the tag which the container is tagged with in your ECR repository.
The new tag will be the GUID of the build which produced the image. 
You can use this GUID to track back which code build action actually built the container.

open `/app/index.html` and add some text to the body of the html document to visualize changes made.

Push the changes to git

    git add .
    git commit -m "Update pipeline to tag container with build number"
    git push origin master

There are a few files which are needed for the next process.

* ECS task definition
* ECS service definition
* Code Deploy deployment group
* Code Deploy appspec

These files currently exist in the `/configs` directory. Also in this directory we have a python script produce-configs.py.

Once your previous push has completed and is built.

This script will produce the correct configs needed for the deployment. This script will query the previous environment we deploy to populate variables.

You will need to pass in the most currently docker image tag.

    python produce-configs.py fargate-dev-workshop test <aws acc number>dkr.ecr.<aws region>.amazonaws.com/fargate-dev-workshop:<gui>

Once we have created the necessary config files we can begin to create our new service.

#### Create ECS service

    aws ecs create-service --region  --service-name fargate-dev-workshop-test --cli-input-json file://./service-definition-test.json

#### Create Code Deploy application

    aws deploy create-application --region $AWS_REGION --application-name fargate-dev-workshop-test --compute-platform ECS


#### Create Code Deploy deployment groups

    aws deploy create-deployment-group --region $AWS_REGION \
     --deployment-group-name ecs-fargate-workshop-test-dg --cli-input-json file://./deployment-group-test.json

#### Deployment changes

    aws ecs deploy --region $AWS_REGION --service 'fargate-dev-workshop-test'  \
     --cluster 'fargate-dev-workshop-test' --codedeploy-application 'fargate-dev-workshop-test' \
     --codedeploy-deployment-group 'ecs-fargate-workshop-test-dg' \
     --task-definition task-definition-test.json --codedeploy-appspec appsectest.json

You will now be able to monitor your deployment in the AWS Code Deploy Console.

In this lab we ran the steps which may be ran as part of a CI/CD pipeline to deploy the updated container. Using modern deployment techniques (Canary, Blue / Green) in also assist in ensuring in the reduction of errors occurring in a production deployment. 
