---
title: "Lab 2: Deploy Docker Image to ECR"
date: 2020-04-10T11:09:29-06:00
weight: 45
---

_Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. SPDX-License-Identifier: CC-BY-SA-4.0_

In this lab we will review the pipeline, connect to our IDE to the Git repository, and make our initial commit.

### Pipeline Review

The pipeline is made up of 4 different steps:
    
    1 - The pipeline is triggered by push to the master branch of the git repository.
    2 - The Dockerfile in the repository linted to check for usage of best practices.
    3 - The code repository is scanned for secrets / passwords to ensure no sensitive information present
    4 - The container is then built and pushed to a container repository (ECR)

In our pipeline if there are any failures (Non-Best practices or secrets found) the build will fail. This will help us ensure only good code gets to production.
        
![Pipeline Architecture](/images/fargate-dev-cicd-pipeline.png)
    
### Connect to GIT (CodeCommit)

Let's connect to the a Git repository. We'll do this manually as setting up development tools is often done by hand.
In the console, navigate to CodeCommit.
Follow the instructions on the console to clone your new repo into a local folder in Cloud9.

#### Initial Push
    
    cd ~/environment/fargate-dev-workshop
    git init . 
    git add remote origin <Your_Repo_Url>
    git add .
    git commit -m "Initial commit"
    git push origin master
    
#### Monitor your pipeline

In the AWS Console, navigate Code Pipeline and select your pipeline.

Your pipeline should have failed in the linting stage.
For more information, on the linting stage click `details`, then `Link to execution details`.
You should be able to see the log for the pipeline.

You can view the reasons why the build failed. In our case, this is due the `:latest` container tag.
    
#### Review Dockerfile best practices

It is a best practice not to use the `:latest` tag when referencing a container image.
For similar reasons, its also suggested to specify version of specific package you install in your containers.
By not using `:latest`, you are limiting the chance of an package or base container image being updated and deployed without your knowledge.

If you do not specify a `USER` in a Dockerfile, the container will have the permission set of `ROOT` . 
It is best practice to ensure the container is limited to using least privilege. 

Later in this workshop we will also review other considerations to account for when thinking of least privilege access and containers.

Fargate also has certain minimum and maximum RAM and CPU which can be assigned to a task in ECS.
To see the `Supported Configurations` section of https://aws.amazon.com/fargate/pricing/

In the Dockerfile located at `~/environment/fargate-dev-workshop/Dockerfile` change the following:
before:

    FROM httpd:latest
    RUN apk -q add libcap
    
after:

    FROM httpd:2.4-alpine
    RUN apk -q add libcap=2.27-r0 --no-cache

Push the changes to git

    git add .
    git commit -m "fixed docker FROM to a pinned version"
    git push origin master

It is important to automate the validation of artifacts and that they are compliant with best practices and your companies standards. This will reduce the chance of an unknown change getting deployed.
