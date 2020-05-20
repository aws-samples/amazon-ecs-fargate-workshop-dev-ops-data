# Fargate for Devs

_// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. // SPDX-License-Identifier: CC-BY-SA-4.0_

## Lab 1: Prerequisites

First, we'll use the [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) to deploy some prerequisites.  Our guiding principle is that we'll use the CDK to deploy static infrastructure and prerequisites that are out of scope for this lab, and use a CI/CD pipeline to deploy the rest.  For example, if we're building a stream processor, we might assume that the Kafka cluster is already in operation, but we need to deploy our actual stream processing application.

#### Note your account and region

Pick an AWS region to work in, such as `us-west-2`.  We'll refer to this as `REGION` going forward.

Also note your AWS account number.  You find this in the console or by running `aws sts get-caller-identity` on the CLI.  We'll refer to this as `ACCOUNT` going forward.

#### Set up a Cloud9 IDE

In the AWS console, go to the Cloud9 service and select `Create environment`.  Call your new IDE `FargateIDE` and click `Next Step`.  On the next screen, change the instance type to `m4.large` and click `Next step` again.  On the final page, click `Create environment`.  Make sure that you leave the VPC settings at the default values.

Once the environment builds, you'll automatically redirect to the IDE.  Take a minute to explore the interface, and note that you can change the color scheme if you like (AWS Cloud9 menu -> Preferences -> Themes).

Next, let's update the Cloud9 environment to let you run the labs from the environment.

* Go to the IAM console and create an instance profile for the Cloud 9 VM.  
    * Go to the `Roles` section.
    * Click `Create role`.
    * Select `AWS service` for the entity and leave the service set to `EC2`.
    * On the next screen, choose `Create policy`.
    * Switch to the JSON tab and paste in the contents of the file `cloud9-iam.json`.
    * Call the policy `Cloud9-fargate-policy`.
    * Click `Create policy`.
    * Switch back to the browser tab with the new role, and assign the policy you just made.
    * Call the role `Cloud9-fargate-role`.
    * Click `Create role`.
* Once this new profile is created, go to EC2 and find the Cloud9 instance, and assign the instance profile to this instance.
* Go to Cloud9 Preferences and under AWS Credentials disable `AWS managed temporary credentials`.  

#### Deploy other prerequisites using CDK

Git clone the workshop repo:

    git clone https://github.com/aws-samples/amazon-ecs-fargate-workshop-dev-ops-data
    mkdir ~/environment/fargate-dev-workshop
    cp -r ~/environment/amazon-ecs-fargate-workshop-dev-ops-data/labs/fargate-dev-workshop/* ~/environment/fargate-dev-workshop/
    cd ~/environment/fargate-dev-workshop

In your Cloud 9 environment, install the CDK and update some dependencies:

    npm install -g aws-cdk@1.19.0
    
Update to the latest version of pip

    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py

Now we install some CDK modules.

    pip install awscli
    pip install --upgrade aws-cdk.core
    pip install -r requirements.txt

Create the file `~/.aws/config` with these lines:

    [default]
    region=REGION
    account=ACCOUNT

Set environment variables which will be used later

    AWS_REGION=`aws configure get region`
    echo $AWS_REGION
    
We're now ready to deploy the prerequisites.  Run the following, making sure to substitute the proper values for your `ACCOUNT` and `REGION`.

    touch ~/.aws/credentials
    cdk bootstrap aws://ACCOUNT/REGION
    cdk synth
    cdk deploy pipeline-to-ecr

## Lab 2: Deploy Docker image to ECR

#### Pipeline Review

The pipeline is made up of 4 different steps:
    
    1 - the pipeline is triggered by commit to the master branch of the git repository.
    2 - the container is linted to check for usage of best practices 
    3 - the container is scanned for secrets / passwords to ensure no secrets are store in the container
    4 - the container is built and pushed to a container repository (ECR)
        
pipeline image here
    
### Connect to GIT (CodeCommit)

Let's connect to the a Git repository. We'll do this manually as setting up development tools is often done by hand.
In the console, navigate to CodeCommit.

Follow the instructions on the console to clone your new repo into a local folder in Cloud9.

#### Initial Push
    
    git init . 
    git remote add origin <CodeCommit_Repo>
    git add .
    git commit -m "Initial commit"
    git push origin master
    
#### Monitor your pipeline

In the AWS Console navigate Code Pipeline
Select your pipeline.

Your pipeline should have failed in the linting stage.
For more information, on the linting stage click details, then Link to execution details.
You should be able to see the log for the set in the pipeline.
    
#### Dockerfile best practices

It is a best practice to not use the :latest tag when referencing container.
This can cause issues of having an unwanted version deployed.

Similar to ensuring you do not use the :latest tag for your containers. 
It is also suggested to specify package version you install on your containers.
You want to avoid the chance of an unwanted package being deployed.

If you do not specify a USER in a Dockerfile, the container will run as ROOT permissions. 
It is best practice to ensure the container is limited to least privilege. 
This will be reviewed later when we dive into the ECS task definition.

In the Dockerfile change the following
before

    FROM httpd:latest
    RUN apk -q add libcap
after

    FROM httpd:2.4.41
    RUN apk -q add libcap=2.27-r0 --no-cache
    
These changes ensure we are pulling a certain version of the base docker image as well as the package we are adding to our container.

Push your changes

    git add .
    git commit -m "fixed docker FROM to a pinned version"
    git push origin master

## Lab 3: Deploy ECS / Farate cluster

#### Infrastrcuture Deployment

Before we deploy our VPC, ECS cluster, and service; lets enable CloudWatch container insights.
Container insights is a very useful feature which allows you to gain insights of resource usage of your containers.

Running the following command will turn on CloudWatch container insights for all ECS clusters which will be deployed into this AWS acccount.

    aws ecs put-account-setting --name "containerInsights" --value "enabled"
    
Now we will deploy Test Environment Stack

    cdk deploy ecs-inf-test
    
This stack will deploy the VPC, ECS Cluster, Load Balancer, and AutoScaling groups.

When the stack has finished deploying it should display the output of the load balancers url.
    
    ecs-inf-test.lburl = ecs-i-loadb-11111111-11111111.us-west-2.elb.amazonaws.com
    
Open a web browers and navigate to the load balancers url provided.
    
## Lab 4: Blue/Green deploy to ECS

In this lab you will update our container image and then deploy in a Blue / Green fashion.

Before you can do that, you will delete the service we just deployed.
Using the AWS console navigate to the ECS console select the cluster for the workshop.
Select the Service deployed and delete it
Go to Tasks, and stop all running tasks.

#### Navigate back configs

In your Cloud9 editior, open the file configs/docker_build_base.yml.

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
The new tag will be the build guid which produced the image. 
You can also use this guid to track back which code build action actually built the container.

open /app/index.html and add some text to the body of the html to visualize changes made.

Push your changes

    git add .
    git commit -m "Update pipeline to tag container with build number"
    git push origin master

There are a few files which are needed for the next process.

* ECS task definition
* ECS service definition
* Code Deploy deployment group
* Code Deploy appspec

These files currect exist in the /configs directory. Also in this directory we have a python script produce-configs.py.

Once your previous push has completed and is built.

This script will produce the correct configs needed for the deployment. This script will query the previous environment we deploy to populate variables.
You will need to pass in the most currect docker image tag.

    python produce-configs.py fargate-dev-workshop test <aws acc number>dkr.ecr.<aws region>.amazonaws.com/fargate-dev-workshop:<gui>

Once we have created the nessessary config files we can begin to create our new service.

#### Create ECS service

    aws ecs create-service --region us-west-2 --service-name fargate-dev-workshop-test --cli-input-json file://./service-definition-test.json

#### Create Code Deploy application

    aws deploy create-application --region us-west-2 --application-name fargate-dev-workshop-test --compute-platform ECS


#### Create Code Deploy deployment groups

    aws deploy create-deployment-group --region us-west-2 \
     --deployment-group-name ecs-fargate-workshop-test-dg --cli-input-json file://./deployment-group-test.json

#### Deployment changes

    aws ecs deploy --region us-west-2 --service 'fargate-dev-workshop-test'  \
     --cluster 'fargate-dev-workshop-test' --codedeploy-application 'fargate-dev-workshop-test' \
     --codedeploy-deployment-group 'ecs-fargate-workshop-test-dg' \
     --task-definition task-definition-test.json --codedeploy-appspec appsectest.json

You will now be able to monitor your deployment in the AWS Code Deploy Console.
        
## Lab 5: Container Observability.

#### deploy cloudformation to create some traffic. replace the `ParameterValue` with your specific load balancer.

    aws cloudformation create-stack --stack-name ecs-fargate-workshop-traffic \
        --template-body file://./r53_health_check.yaml \
        --parameters  ParameterKey=url,ParameterValue="YOUR LOAD BALANCE URL"
        
Navigate to the CloudWatch console.
Near the top left of the page where the "Overview" drop down menu is, select container insights.
In the drop down menu under container insights, take a look at the different metrics captured by ECS Service, ECS Cluster, and ECS Task.

You are able to select a time frame from the graphs and also view the container logs from the time you specified.

## Lab 6: Update Task Definition

### Review Task Def

Ensure the container is running without elevated privileged. 
The default is false, however its suggested to also explicitly state this in your task defintion.
    
    "privileged": true|false

#### Linux Capacitlies
Linux Capacities applies to what docker privileges the container has on a host. It is best practice to also apply least privilege what the commands the container can send docker. For example the the container should not need access to the logs, when logging to stderr and stdout docker will take care of this for the container. The container should not need access to edit the network, this is provided for the container. In this example we are dropping some of the most privileged capabilities.

    "linuxParameters": {
      "capabilities": {
        "drop": ["SYS_ADMIN","NET_ADMIN"]
        }
    }
    
#### ulimits
Amazon ECS task definitions for Fargate support the ulimits parameter to define the resource limits to set for a container.

Fargate tasks use the default resource limit values with the exception of the nofile resource limit parameter, which Fargate overrides. 
The nofile resource limit sets a restriction on the number of open files that a container can use. 
The default nofile soft limit is 1024 and hard limit is 4096 for Fargate tasks. These limits can be adjusted in a task definition if your tasks needs to handle a larger number of files.

    "ulimits": [
        {
            "name": "cpu",
            "softLimit": 0,
            "hardLimit": 0
        }
    ],
    
Run the following commands to update the task defintion which you will deploy. 
Due to low utilization, reconfiguring the task to use the smallest amount of compute for fargate.

open /app/index.html and add some text to the body of the html to visualize changes made.

Push your changes

    git add .
    git commit -m "Update pipeline to tag container with build number"
    git push origin master
    
Wait for the container to be published in ECR. 
The run the following commands in the /configs/ directory:

    sed -i '/cpu/c\   \"cpu\" : \":256\",' task-definition-test.json
    sed -i '/memory/c\   \"memory\" : \"512\",' task-definition-test.json
    sed -i '/image/c\   \"image\" : \"YOUR-CONTAINER-REPO:BUILD-GUID\",' task-definition-test.json 

Deploy the updated container and task definition specifying fewer resources.

    aws ecs deploy --region us-west-2 --service 'fargate-dev-workshop-test'  \
     --cluster 'fargate-dev-workshop-test' --codedeploy-application 'fargate-dev-workshop-test' \
     --codedeploy-deployment-group 'ecs-fargate-workshop-test-dg' \
     --task-definition task-definition-test.json --codedeploy-appspec appsectest.json

## Lab 7: Clean up.

    aws deploy delete-deployment-group --deployment-group-name 'ecs-fargate-workshop-test-dg' --application-name fargate-dev-workshop-test
    aws deploy delete-application --application-name fargate-dev-workshop-test
    aws cloudformation delete-stack --stack-name ecs-fargate-workshop-traffic
    cdk destroy ecs-inf-test
    cdk destroy pipeline-to-ecr
