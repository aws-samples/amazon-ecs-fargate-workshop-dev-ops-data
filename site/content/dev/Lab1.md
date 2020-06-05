---
title: "Lab 1: Prerequisites"
date: 2020-04-10T11:08:42-06:00
weight: 35
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

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
    * Switch to the JSON tab and paste in the contents of the file [cloud9-iam.json](https://raw.githubusercontent.com/aws-samples/amazon-ecs-fargate-workshop-dev-ops-data/master/labs/cloud9-iam.json).
    * Call the policy `Cloud9-fargate-policy`.
    * Click `Create policy`.
    * Switch back to the browser tab with the new role, and assign the policy you just made.
    * Call the role `Cloud9-fargate-role`.
    * Click `Create role`.
* Once this new profile is created, go to EC2 and find the Cloud9 instance, and assign the instance profile to this instance.
* Go to Cloud9 Preferences and under AWS Credentials disable `AWS managed temporary credentials`.  

#### Deploy other prerequisites using CDK

Clone the Git repo:

    git clone https://github.com/aws-samples/amazon-ecs-fargate-workshop-dev-ops-data
    
We will be committing portions of this repo during this lab. To make it easier we will copy the used portions of the content to a separate location.

    mkdir ~/environment/fargate-dev-workshop
    cp -r ~/environment/amazon-ecs-fargate-workshop-dev-ops-data/labs/fargate-dev-workshop/* ~/environment/fargate-dev-workshop/
    cd ~/environment/fargate-dev-workshop
    
For the rest of the labs in this track we will be working in the directory `~/environment/fargate-dev-workshop`

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

In this lab we deployed our Cloud9 IDE which we will use for the remainder of the workshop as well as deployed our initial pipeline which will build our containers. 
