---
title: "Lab 1: Environment"
date: 2020-04-10T11:14:49-06:00
weight: 5
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

First lab is focused on deploying all  prerequisites for AWS ECS Fargate lab for Operations Teams. For the purpose of this lab we will use following AWS services and software components:
* [Cloud9 IDE](https://aws.amazon.com/cloud9/)
* [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) (Cloud Development Kit)
* [Amazon ECS](https://aws.amazon.com/ecs/) (Amazon Elastic Container Service) 
  
First, we'll use the [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html) to deploy some prerequisites.  Our guiding principle is that we'll use the CDK to deploy static infrastructure and prerequisites.

### Note your account and region

Pick an AWS region to work in, such as `us-west-2`.  We'll refer to this as `REGION` going forward.

Also note your AWS account number.  You find this in the console or by running `aws sts get-caller-identity` on the CLI.  We'll refer to this as `ACCOUNT` going forward.

### Set up a Cloud9 IDE

In the AWS console, go to the Cloud9 service and select `Create environment`.  Call your new IDE `FargateIDE` and click `Next Step`.  On the next screen, change the instance type to `t2.micro` and click `Next step` again.  On the final page, click `Create environment`.  Make sure that you leave the VPC settings at the default values.

Once the environment builds, you'll automatically redirect to the IDE.  Take a minute to explore the interface, and note that you can change the color scheme if you like (AWS Cloud9 menu -> Preferences -> Themes).

Next, let's update the Cloud9 environment to let you run the labs from the environment.


* Create a role for your Cloud9 environment by clicking on the following [link](https://console.aws.amazon.com/iam/home#/roles$new?step=review&commonUseCase=EC2%2BEC2&selectedUseCase=EC2&policies=arn:aws:iam::aws:policy%2FAdministratorAccess)
* Confirm that AWS service and EC2 are selected, then click Next to view permissions.
* Confirm that AdministratorAccess is checked, then click Next: Tags to assign tags.
* Take the defaults, and click Next: Review to review.
* Enter `Cloud9-fargate-role` for the Name, and click Create role. 

* Once this new profile is created, go to EC2 and find the Cloud9 instance, and assign the instance profile to this instance.
* Go to Cloud9 Preferences and under AWS Credentials disable `AWS managed temporary credentials`.  

### Deploy other prerequisites using CDK

In your Cloud 9 environment, install the CDK and update some dependencies:

    npm install -g aws-cdk@1.19.0

Next clone the Git repo:

    git clone https://github.com/aws-samples/amazon-ecs-fargate-workshop-dev-ops-data.git fargate-workshop-ops
    cd fargate-workshop-ops

Next we need to create a Python virtual environment.

    virtualenv .env
    source .env/bin/activate

Now we install some CDK modules.

    pip install awscli
    pip install --upgrade aws-cdk.core
    pip install -r labs/requirements.txt

Create the file `~/.aws/config` with these lines:

    [default]
    region=REGION
    account=ACCOUNT

We're now ready to deploy the prerequisites.

    cd ~/environment/fargate-workshop/labs/fargate-ops-cdk
    touch ~/.aws/credentials

Verify that cdk version is at least 1.23.0

    cdk version

Proceed to initial deployment.  Run the following, making sure to substitute the proper values for your `ACCOUNT` and `REGION`.

    cdk bootstrap aws://ACCOUNT/REGION
    cdk synth
    cdk deploy FargateWorkshopOps-base
    cdk deploy FargateWorkshopOps-cluster


This is what we'll have after the deployment is complete:

* A VPC with private and public subnets
* A service discovery system based on AWS CloudMap
* Cloud9 IDE environment
